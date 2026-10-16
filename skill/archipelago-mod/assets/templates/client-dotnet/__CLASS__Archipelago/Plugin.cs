using ArchipelagoBridge;
using BepInEx;
using BepInEx.Configuration;
using HarmonyLib;

namespace __CLASS__Archipelago
{
    [BepInPlugin(PluginGuid, "__GAME_NAME__ Archipelago", PluginVersion)]
    public sealed class Plugin : BaseUnityPlugin
    {
        const string PluginGuid = "archipelago.__MODULE__";
        const string PluginVersion = "0.1.0";

        /// <summary>Reached by Harmony patches to report checks and deaths.</summary>
        internal static ArchipelagoConnection Connection { get; private set; }

        void Awake()
        {
            var server = Config.Bind("Connection", "Server", "localhost:38281", "Archipelago server address");
            var slot = Config.Bind("Connection", "Slot", "Player1", "Slot name from your YAML");
            var password = Config.Bind("Connection", "Password", "", "Room password, empty if none");

            Connection = new ArchipelagoConnection(
                "__GAME_NAME__",
                new ConnectionSettings(server.Value, slot.Value, password.Value),
                new GameAdapter(Logger));
            new Harmony(PluginGuid).PatchAll();
        }

        void Update() => Connection.Update();
    }
}
