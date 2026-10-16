namespace ArchipelagoBridge
{
    /// <summary>
    /// DeathLink bookkeeping without network or game code: holds a received death until the game can apply it, and
    /// swallows the one death that applying it causes, so it is never sent back to the multiworld.
    /// </summary>
    public sealed class DeathLinkGate
    {
        readonly object pendingLock = new object();
        string pendingCause;
        bool ownKillInProgress;

        /// <summary>Thread-safe: called from the network thread.</summary>
        public void OnDeathReceived(string cause)
        {
            lock (pendingLock)
            {
                pendingCause = cause;
            }
        }

        /// <summary>Returns the cause of a death to apply now, or null.</summary>
        public string TakePendingDeath()
        {
            lock (pendingLock)
            {
                var cause = pendingCause;
                pendingCause = null;
                return cause;
            }
        }

        /// <summary>The game accepted the kill: the next reported death is ours.</summary>
        public void OnKillApplied() => ownKillInProgress = true;

        /// <summary>Returns false for the death caused by a received DeathLink, true for a real one.</summary>
        public bool ShouldSendDeath()
        {
            if (!ownKillInProgress)
                return true;
            ownKillInProgress = false;
            return false;
        }

        /// <summary>Leaving gameplay or the connection drops: stale deaths must not kill the player later.</summary>
        public void Reset()
        {
            TakePendingDeath();
            ownKillInProgress = false;
        }
    }
}
