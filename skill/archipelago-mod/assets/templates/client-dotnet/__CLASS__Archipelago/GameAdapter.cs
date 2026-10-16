using System;
using System.Collections.Generic;
using ArchipelagoBridge;
using BepInEx.Logging;

namespace __CLASS__Archipelago
{
    /// <summary>
    /// The only game-specific glue. Each member names what must be found in the game (see docs/dev/game-map.md),
    /// and throws until it is implemented so a missing piece fails loudly instead of silently doing nothing.
    /// </summary>
    sealed class GameAdapter : IGameAdapter
    {
        readonly ManualLogSource logger;

        public GameAdapter(ManualLogSource logger)
        {
            this.logger = logger;
        }

        // Find: the object that exists only while a save is loaded and gameplay is running.
        public bool IsInGame => throw new NotImplementedException(nameof(IsInGame));

        // Find: save fields the mod can own (a custom key in the save dictionary, or a side file written in the same
        // moment as the game saves) for the seed binding and the applied item count.
        public string BoundSaveKey
        {
            get => throw new NotImplementedException(nameof(BoundSaveKey));
            set => throw new NotImplementedException(nameof(BoundSaveKey));
        }

        public int AppliedItemCount
        {
            get => throw new NotImplementedException(nameof(AppliedItemCount));
            set => throw new NotImplementedException(nameof(AppliedItemCount));
        }

        // Find: the save flags behind each location in data.py, mapped to their location IDs.
        public IEnumerable<long> ReadCompletedLocations() =>
            throw new NotImplementedException(nameof(ReadCompletedLocations));

        // Find: the flag set when the goal is beaten.
        public bool IsGoalComplete() => throw new NotImplementedException(nameof(IsGoalComplete));

        // Find: the game's own "add item to inventory" method, called with the item matching each item ID.
        public bool TryGrantItem(long itemId, string itemName, string senderName) =>
            throw new NotImplementedException(nameof(TryGrantItem));

        // Find: the method the game calls to kill the player, and when it is safe to call it.
        public bool TryKillPlayer(string cause) => throw new NotImplementedException(nameof(TryKillPlayer));

        // Replace with the game's notification UI once found; the log is the fallback.
        public void ShowMessage(string message) => logger.LogInfo(message);
    }
}
