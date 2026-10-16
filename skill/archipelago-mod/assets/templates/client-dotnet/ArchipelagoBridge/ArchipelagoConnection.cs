using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Archipelago.MultiClient.Net;
using Archipelago.MultiClient.Net.BounceFeatures.DeathLink;
using Archipelago.MultiClient.Net.Enums;
using Archipelago.MultiClient.Net.Models;

namespace ArchipelagoBridge
{
    /// <summary>
    /// Game-agnostic Archipelago client: connection and reconnection, item granting, location checks, goal and
    /// DeathLink. Call <see cref="Update"/> once per frame from the game thread; everything that touches the game
    /// goes through <see cref="IGameAdapter"/> from that call, so network threads never touch game state.
    /// </summary>
    public sealed class ArchipelagoConnection
    {
        // Spreading grants over frames keeps a large backlog (first connection, long offline session) from stalling
        // the game or overflowing its notification queue.
        const int MaxItemsGrantedPerUpdate = 1;
        const string DeathLinkSlotDataKey = "death_link";

        readonly string gameName;
        readonly ConnectionSettings settings;
        readonly IGameAdapter game;
        readonly ReconnectBackoff backoff = new ReconnectBackoff();
        readonly DeathLinkGate deathLinkGate = new DeathLinkGate();

        // Written by game-hook threads, drained by Update.
        readonly object pendingLock = new object();
        readonly HashSet<long> pendingLocations = new HashSet<long>();

        ArchipelagoSession session;
        ArchipelagoSession connectingSession;
        Task<LoginResult> login;
        DeathLinkService deathLink;
        string saveKey;
        DateTime nextAttemptUtc = DateTime.MinValue;
        bool saveChecked;
        bool saveUsable;
        bool goalSent;

        public ArchipelagoConnection(string gameName, ConnectionSettings settings, IGameAdapter game)
        {
            this.gameName = gameName;
            this.settings = settings;
            this.game = game;
        }

        public bool IsConnected => session != null && session.Socket.Connected;

        /// <summary>Thread-safe: may be called from a Harmony patch or from any game thread.</summary>
        public void ReportLocationChecked(long locationId)
        {
            lock (pendingLock)
            {
                pendingLocations.Add(locationId);
            }
        }

        /// <summary>Call on the game thread whenever the player dies.</summary>
        public void ReportDeath(string cause)
        {
            // deathLink is null unless the player enabled DeathLink: a disabled player must never kill others.
            if (deathLinkGate.ShouldSendDeath() && deathLink != null && saveUsable)
                deathLink.SendDeathLink(new DeathLink(settings.SlotName, cause));
        }

        public void Update()
        {
            if (!IsConnected)
            {
                UpdateConnection();
                return;
            }

            if (!game.IsInGame)
            {
                saveChecked = false;
                saveUsable = false;
                deathLinkGate.Reset();
                return;
            }

            if (!saveChecked)
            {
                saveUsable = BindSave();
                saveChecked = true;
            }
            if (!saveUsable)
                return;

            SendPendingLocations();
            GrantReceivedItems();
            ApplyReceivedDeath();
            SendGoalOnce();
        }

        bool BindSave()
        {
            switch (SaveBinding.Check(game.BoundSaveKey, saveKey))
            {
                case SaveBindingState.BelongsElsewhere:
                    game.ShowMessage("This save belongs to another Archipelago seed or slot: load the right save");
                    return false;
                case SaveBindingState.Unbound:
                    game.BoundSaveKey = saveKey;
                    break;
            }
            // Checks made while offline only exist in the save: resend them all, the server ignores duplicates.
            foreach (var locationId in game.ReadCompletedLocations())
                ReportLocationChecked(locationId);
            return true;
        }

        void UpdateConnection()
        {
            if (session != null)
                OnDisconnected();

            if (login == null)
            {
                if (DateTime.UtcNow >= nextAttemptUtc)
                    StartLogin();
                return;
            }

            if (!login.IsCompleted)
                return;

            var result = login.IsFaulted ? new LoginFailure(login.Exception.GetBaseException().Message) : login.Result;
            login = null;

            if (result is LoginSuccessful success)
                OnConnected(success);
            else
                OnLoginFailed((LoginFailure)result);
        }

        void StartLogin()
        {
            try
            {
                connectingSession = ArchipelagoSessionFactory.CreateSession(settings.Server);
            }
            catch (UriFormatException e)
            {
                OnLoginFailed(new LoginFailure($"invalid server address '{settings.Server}': {e.Message}"));
                return;
            }

            var newSession = connectingSession;
            var password = string.IsNullOrEmpty(settings.Password) ? null : settings.Password;
            // TryConnectAndLogin blocks until the server answers; it must never run on the game thread.
            login = Task.Run(() => newSession.TryConnectAndLogin(
                gameName, settings.SlotName, ItemsHandlingFlags.AllItems, password: password));
        }

        void OnConnected(LoginSuccessful success)
        {
            session = connectingSession;
            connectingSession = null;
            backoff.Reset();
            saveKey = SaveBinding.KeyFor(session.RoomState.Seed, success.Slot);
            saveChecked = false;
            saveUsable = false;
            goalSent = false;
            deathLinkGate.Reset();

            if (IsEnabled(success.SlotData, DeathLinkSlotDataKey))
            {
                deathLink = session.CreateDeathLinkService();
                deathLink.OnDeathLinkReceived += received =>
                    deathLinkGate.OnDeathReceived(received.Cause ?? $"{received.Source} died");
                deathLink.EnableDeathLink();
            }

            game.ShowMessage($"Connected to Archipelago as {settings.SlotName}");
        }

        void OnLoginFailed(LoginFailure failure)
        {
            // A refused login leaves the socket open: close it, or every retry leaks one.
            CloseQuietly(connectingSession);
            connectingSession = null;
            var delay = backoff.NextDelayAfterFailure();
            nextAttemptUtc = DateTime.UtcNow + delay;
            game.ShowMessage(
                $"Archipelago connection failed ({string.Join(", ", failure.Errors)}), retrying in {delay.TotalSeconds}s");
        }

        void OnDisconnected()
        {
            CloseQuietly(session);
            session = null;
            deathLink = null;
            deathLinkGate.Reset();
            nextAttemptUtc = DateTime.UtcNow;
            game.ShowMessage("Archipelago connection lost, reconnecting");
        }

        void SendPendingLocations()
        {
            long[] locationIds;
            lock (pendingLock)
            {
                if (pendingLocations.Count == 0)
                    return;
                locationIds = pendingLocations.ToArray();
                pendingLocations.Clear();
            }
            // A send lost to a disconnect is recovered by the save resync on the next connection.
            session.Locations.CompleteLocationChecksAsync(locationIds);
        }

        void GrantReceivedItems()
        {
            game.AppliedItemCount = ItemGrants.GrantNext(
                session.Items.AllItemsReceived,
                game.AppliedItemCount,
                MaxItemsGrantedPerUpdate,
                (ItemInfo item) => game.TryGrantItem(item.ItemId, item.ItemDisplayName, item.Player?.Name ?? "Server"));
        }

        void ApplyReceivedDeath()
        {
            var cause = deathLinkGate.TakePendingDeath();
            if (cause == null)
                return;
            if (game.TryKillPlayer(cause))
                deathLinkGate.OnKillApplied();
            else
                deathLinkGate.OnDeathReceived(cause);
        }

        void SendGoalOnce()
        {
            if (goalSent || !game.IsGoalComplete())
                return;
            session.SetGoalAchieved();
            goalSent = true;
        }

        static void CloseQuietly(ArchipelagoSession closing)
        {
            // Errors while closing a dead socket carry no information: observe them so they are not rethrown later.
            closing?.Socket.DisconnectAsync().ContinueWith(task => task.Exception, TaskContinuationOptions.OnlyOnFaulted);
        }

        static bool IsEnabled(Dictionary<string, object> slotData, string key) =>
            slotData != null && slotData.TryGetValue(key, out var value) && Convert.ToInt64(value) != 0;
    }
}
