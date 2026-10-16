namespace ArchipelagoBridge
{
    public enum SaveBindingState
    {
        /// <summary>The save was never connected: bind it to this seed and slot.</summary>
        Unbound,
        Matches,
        /// <summary>The save belongs to another seed or slot: touching it would send wrong checks and skip items.</summary>
        BelongsElsewhere,
    }

    /// <summary>Ties a save to one seed and slot, so a save from another multiworld is never synced.</summary>
    public static class SaveBinding
    {
        public static string KeyFor(string seedName, int slot) => $"{seedName}:{slot}";

        public static SaveBindingState Check(string boundKey, string currentKey)
        {
            if (string.IsNullOrEmpty(boundKey))
                return SaveBindingState.Unbound;
            return boundKey == currentKey ? SaveBindingState.Matches : SaveBindingState.BelongsElsewhere;
        }
    }
}
