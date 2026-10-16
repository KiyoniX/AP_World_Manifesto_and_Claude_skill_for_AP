using System;
using Xunit;

namespace ArchipelagoBridge.Tests
{
    public class ReconnectBackoffTests
    {
        [Fact]
        public void DoublesUpToTheCapThenResets()
        {
            var backoff = new ReconnectBackoff();
            var delays = new double[6];
            for (var i = 0; i < delays.Length; i++)
                delays[i] = backoff.NextDelayAfterFailure().TotalSeconds;

            Assert.Equal(new double[] { 2, 4, 8, 16, 30, 30 }, delays);

            backoff.Reset();
            Assert.Equal(TimeSpan.FromSeconds(2), backoff.NextDelayAfterFailure());
        }
    }

    public class DeathLinkGateTests
    {
        [Fact]
        public void TheDeathWeCauseIsNotSentBack()
        {
            var gate = new DeathLinkGate();
            gate.OnDeathReceived("Ann died");

            Assert.Equal("Ann died", gate.TakePendingDeath());
            gate.OnKillApplied();

            Assert.False(gate.ShouldSendDeath());
            Assert.True(gate.ShouldSendDeath());
        }

        [Fact]
        public void APendingDeathIsTakenOnce()
        {
            var gate = new DeathLinkGate();
            gate.OnDeathReceived("Ann died");

            Assert.NotNull(gate.TakePendingDeath());
            Assert.Null(gate.TakePendingDeath());
        }

        [Fact]
        public void ResetDropsStaleDeaths()
        {
            var gate = new DeathLinkGate();
            gate.OnDeathReceived("Ann died");
            gate.OnKillApplied();

            gate.Reset();

            Assert.Null(gate.TakePendingDeath());
            Assert.True(gate.ShouldSendDeath());
        }
    }

    public class SaveBindingTests
    {
        static readonly string Current = SaveBinding.KeyFor("seed-A", 3);

        [Fact]
        public void AFreshSaveIsBound() =>
            Assert.Equal(SaveBindingState.Unbound, SaveBinding.Check("", Current));

        [Fact]
        public void TheSameSeedAndSlotMatch() =>
            Assert.Equal(SaveBindingState.Matches, SaveBinding.Check(SaveBinding.KeyFor("seed-A", 3), Current));

        [Fact]
        public void AnotherSeedOrSlotIsRefused()
        {
            Assert.Equal(SaveBindingState.BelongsElsewhere, SaveBinding.Check(SaveBinding.KeyFor("seed-B", 3), Current));
            Assert.Equal(SaveBindingState.BelongsElsewhere, SaveBinding.Check(SaveBinding.KeyFor("seed-A", 4), Current));
        }
    }
}
