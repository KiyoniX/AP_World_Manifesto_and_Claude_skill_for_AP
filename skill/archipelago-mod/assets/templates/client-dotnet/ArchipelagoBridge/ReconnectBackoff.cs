using System;

namespace ArchipelagoBridge
{
    /// <summary>Delay before the next connection attempt: 2 s, 4 s, 8 s... capped, reset by a success.</summary>
    public sealed class ReconnectBackoff
    {
        public static readonly TimeSpan MaxDelay = TimeSpan.FromSeconds(30);

        int failures;

        public TimeSpan NextDelayAfterFailure()
        {
            failures = Math.Min(failures + 1, 5);
            var delay = TimeSpan.FromSeconds(1 << failures);
            return delay < MaxDelay ? delay : MaxDelay;
        }

        public void Reset() => failures = 0;
    }
}
