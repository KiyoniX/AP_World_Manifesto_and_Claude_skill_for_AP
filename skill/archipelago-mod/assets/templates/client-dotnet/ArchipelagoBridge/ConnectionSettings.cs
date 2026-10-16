namespace ArchipelagoBridge
{
    public sealed class ConnectionSettings
    {
        public ConnectionSettings(string server, string slotName, string password)
        {
            Server = server;
            SlotName = slotName;
            Password = password;
        }

        /// <summary>Host with optional scheme and port, e.g. "archipelago.gg:38281" or "ws://localhost:38281".</summary>
        public string Server { get; }

        public string SlotName { get; }

        /// <summary>Null or empty when the room has no password.</summary>
        public string Password { get; }
    }
}
