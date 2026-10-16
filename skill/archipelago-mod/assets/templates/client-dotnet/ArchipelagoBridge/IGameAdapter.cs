using System.Collections.Generic;

namespace ArchipelagoBridge
{
    /// <summary>
    /// Everything the bridge needs from one specific game. This is the only part rewritten per game:
    /// the bridge itself never references game code, so it is reused unchanged across mods.
    /// Every member is called on the game thread, from <see cref="ArchipelagoConnection.Update"/>.
    /// </summary>
    public interface IGameAdapter
    {
        /// <summary>True while a save is loaded and the game can safely be read, receive items or kill the player.</summary>
        bool IsInGame { get; }

        /// <summary>
        /// The seed and slot the loaded save belongs to (<see cref="SaveBinding.KeyFor"/>), stored inside the save.
        /// Empty for a save that was never connected.
        /// </summary>
        string BoundSaveKey { get; set; }

        /// <summary>
        /// How many received items the loaded save has already granted, stored inside the save and written with it:
        /// reloading an older save must re-grant exactly what that save is missing, never more.
        /// </summary>
        int AppliedItemCount { get; set; }

        /// <summary>Location IDs completed in the loaded save, resent on connect to recover checks made offline.</summary>
        IEnumerable<long> ReadCompletedLocations();

        bool IsGoalComplete();

        /// <summary>
        /// Grants one received item. Return false when the game cannot take it right now (cutscene, loading screen):
        /// the same item is offered again on a later frame. Unknown IDs must be accepted and ignored, not retried.
        /// </summary>
        bool TryGrantItem(long itemId, string itemName, string senderName);

        /// <summary>
        /// Kills the player for a received DeathLink. Return true only if the player will die and the game will report
        /// that death exactly once through <see cref="ArchipelagoConnection.ReportDeath"/>; return false to retry later.
        /// </summary>
        bool TryKillPlayer(string cause);

        void ShowMessage(string message);
    }
}
