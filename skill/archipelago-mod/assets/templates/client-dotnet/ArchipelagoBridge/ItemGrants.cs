using System;
using System.Collections.Generic;

namespace ArchipelagoBridge
{
    /// <summary>Pure item-granting logic, kept apart from the network code so it can be unit tested.</summary>
    public static class ItemGrants
    {
        /// <summary>
        /// Grants received items in server order, starting after <paramref name="appliedCount"/>, and stops at the
        /// first item the game refuses so order is preserved. Returns the new applied count.
        /// </summary>
        public static int GrantNext<T>(IReadOnlyList<T> received, int appliedCount, int maxGrants, Func<T, bool> tryGrant)
        {
            var granted = 0;
            while (appliedCount < received.Count && granted < maxGrants && tryGrant(received[appliedCount]))
            {
                appliedCount++;
                granted++;
            }
            return appliedCount;
        }
    }
}
