using System.Collections.Generic;
using Xunit;

namespace ArchipelagoBridge.Tests
{
    public class ItemGrantsTests
    {
        static readonly IReadOnlyList<int> Received = new[] { 10, 20, 30 };

        [Fact]
        public void GrantsOnlyItemsAfterTheAppliedCount()
        {
            var granted = new List<int>();

            var applied = ItemGrants.GrantNext(Received, 1, 10, item => { granted.Add(item); return true; });

            Assert.Equal(3, applied);
            Assert.Equal(new[] { 20, 30 }, granted);
        }

        [Fact]
        public void StopsAtTheFirstRefusedItemToKeepServerOrder()
        {
            var applied = ItemGrants.GrantNext(Received, 0, 10, item => item != 20);

            Assert.Equal(1, applied);
        }

        [Fact]
        public void RespectsTheGrantBudget()
        {
            var applied = ItemGrants.GrantNext(Received, 0, 2, _ => true);

            Assert.Equal(2, applied);
        }

        [Fact]
        public void NeverGrantsTwiceWhenEverythingIsApplied()
        {
            var applied = ItemGrants.GrantNext(Received, 3, 10, _ => throw new System.InvalidOperationException());

            Assert.Equal(3, applied);
        }
    }
}
