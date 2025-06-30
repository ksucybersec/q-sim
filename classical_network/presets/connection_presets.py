from classical_network.config.connection_config import ConnectionConfig, _generate_description

# --- Wired ---
GIGABIT_ETHERNET = ConnectionConfig(
    bandwidth=1e9,  # 1 Gbps
    latency=50e-6,  # 0.05 ms (typical for short L2 link, can vary)
    packet_loss_rate=1e-7, # Very low for stable wired
    packet_error_rate=1e-9, # Very low
    mtu=1500,
    description=_generate_description("Gigabit Ethernet", 1000, 0.05, 1e-7, 1e-9, 1500)
)

FAST_ETHERNET = ConnectionConfig(
    bandwidth=100e6, # 100 Mbps
    latency=100e-6, # 0.1 ms
    packet_loss_rate=5e-7,
    packet_error_rate=5e-8,
    mtu=1500,
    description=_generate_description("Fast Ethernet", 100, 0.1, 5e-7, 5e-8, 1500)
)

FIBER_OPTIC_LONG_HAUL = ConnectionConfig(
    bandwidth=100e9, # 100 Gbps (can be much higher)
    latency=50e-3,  # 50 ms (e.g., trans-continental, ~10,000 km at 2/3 c)
                    # Speed of light in fiber is approx 2e8 m/s. 10,000 km / 2e8 m/s = 0.05s
    packet_loss_rate=1e-9, # Extremely low for well-maintained fiber
    packet_error_rate=1e-12, # Extremely low
    mtu=9000,       # Often supports Jumbo Frames
    description=_generate_description("Fiber Optic (Long Haul)", 100000, 50, 1e-9, 1e-12, 9000)
)

FIBER_OPTIC_METRO = ConnectionConfig(
    bandwidth=10e9, # 10 Gbps
    latency=1e-3,   # 1 ms (e.g., within a city)
    packet_loss_rate=1e-8,
    packet_error_rate=1e-11,
    mtu=9000,
    description=_generate_description("Fiber Optic (Metro)", 10000, 1.0, 1e-8, 1e-11, 9000)
)

COAXIAL_CABLE_MODEM = ConnectionConfig(
    bandwidth=500e6, # 500 Mbps (downstream, can vary widely with DOCSIS versions)
    latency=10e-3,  # 10 ms (typical for cable internet, shared medium)
    packet_loss_rate=1e-4, # Higher than fiber due to noise, shared medium
    packet_error_rate=1e-5,
    mtu=1500,
    description=_generate_description("Coaxial Cable Modem", 500, 10.0, 1e-4, 1e-5, 1500)
)

DSL_MODEM = ConnectionConfig(
    bandwidth=20e6,  # 20 Mbps (ADSL2+, can vary)
    latency=25e-3,  # 25 ms
    packet_loss_rate=5e-4,
    packet_error_rate=1e-4,
    mtu=1492,       # Often PPPoE adds overhead
    description=_generate_description("DSL Modem", 20, 25.0, 5e-4, 1e-4, 1492)
)

# --- Wireless ---
WIFI_802_11AC_IDEAL = ConnectionConfig(
    bandwidth=400e6, # 400 Mbps (realistic for a good connection, theoretical is higher)
    latency=5e-3,   # 5 ms (can vary greatly with interference, distance)
    packet_loss_rate=1e-3, # 0.1% (higher due to interference, contention)
    packet_error_rate=5e-4, # More prone to errors
    mtu=1500, # Can be up to 2304, but 1500 is common for compatibility
    description=_generate_description("WiFi 802.11ac (Ideal)", 400, 5.0, 1e-3, 5e-4, 1500)
)

WIFI_802_11N_AVERAGE = ConnectionConfig(
    bandwidth=50e6,  # 50 Mbps
    latency=20e-3,  # 20 ms
    packet_loss_rate=5e-3, # 0.5%
    packet_error_rate=1e-3,
    mtu=1500,
    description=_generate_description("WiFi 802.11n (Average)", 50, 20.0, 5e-3, 1e-3, 1500)
)

CELLULAR_4G_LTE_GOOD = ConnectionConfig(
    bandwidth=50e6,  # 50 Mbps
    latency=50e-3,  # 50 ms
    packet_loss_rate=1e-3, # 0.1%
    packet_error_rate=5e-4,
    mtu=1500, # Network may use smaller internally but 1500 is typical IP MTU
    description=_generate_description("Cellular 4G/LTE (Good)", 50, 50.0, 1e-3, 5e-4, 1500)
)

CELLULAR_5G_MMWAVE_IDEAL = ConnectionConfig(
    bandwidth=1e9,    # 1 Gbps (can be higher, but this is a good ideal figure)
    latency=5e-3,     # 5 ms (low latency is a key 5G feature)
    packet_loss_rate=5e-4, # Can still have loss due to mobility/blockage
    packet_error_rate=1e-4,
    mtu=1500, # Or higher with network slicing configurations
    description=_generate_description("Cellular 5G mmWave (Ideal)", 1000, 5.0, 5e-4, 1e-4, 1500)
)

SATELLITE_GEOSTATIONARY = ConnectionConfig(
    bandwidth=25e6,  # 25 Mbps (e.g., HughesNet, Starlink is LEO and different)
    latency=600e-3, # 600 ms (very high due to distance to GEO orbit ~35,786 km * 2)
    packet_loss_rate=1e-2, # 1% (prone to weather interference)
    packet_error_rate=5e-3,
    mtu=1500,
    description=_generate_description("Satellite (Geostationary)", 25, 600.0, 1e-2, 5e-3, 1500)
)

SATELLITE_LEO = ConnectionConfig( # e.g., Starlink
    bandwidth=150e6, # 150 Mbps (varies, can be higher)
    latency=40e-3,   # 40 ms (much lower than GEO)
    packet_loss_rate=5e-3, # Still higher than terrestrial wired
    packet_error_rate=1e-3,
    mtu=1500,
    description=_generate_description("Satellite (LEO - Starlink like)", 150, 40.0, 5e-3, 1e-3, 1500)
)

# --- Special Purpose ---
IDEAL_PERFECT_LINK = ConnectionConfig(
    bandwidth=float('inf'), # Effectively infinite bandwidth
    latency=0.0,            # Zero latency
    packet_loss_rate=0.0,
    packet_error_rate=0.0,
    mtu=65535,              # Max possible IP packet size (without jumbograms)
    description=_generate_description("Ideal Perfect Link", float('inf'), 0.0, 0.0, 0.0, 65535)
)

DIAL_UP_MODEM = ConnectionConfig( # For historical fun or very constrained sims
    bandwidth=56e3,  # 56 Kbps
    latency=150e-3, # 150 ms (can be higher with handshaking)
    packet_loss_rate=5e-3,
    packet_error_rate=1e-3,
    mtu=576,        # Common MTU for dial-up to avoid fragmentation
    description=_generate_description("Dial-up Modem (56k)", 0.056, 150.0, 5e-3, 1e-3, 576)
)

CONFIG_PRESETS = {
    "gigabit_ethernet": GIGABIT_ETHERNET,
    "fast_ethernet": FAST_ETHERNET,
    "fiber_optic_long_haul": FIBER_OPTIC_LONG_HAUL,
    "fiber_optic_metro": FIBER_OPTIC_METRO,
    "coaxial": COAXIAL_CABLE_MODEM,
    "dsl": DSL_MODEM,
    "wifi_802_11ac_ideal": WIFI_802_11AC_IDEAL,
    "wifi_802_11ac_average": WIFI_802_11N_AVERAGE,
    "cellular_4g_good":CELLULAR_4G_LTE_GOOD, 
    "ideal_perfect_link": IDEAL_PERFECT_LINK,
    "perfect_link": IDEAL_PERFECT_LINK,
    "dial_up_modem": DIAL_UP_MODEM
}

DEFAULT_PRESET  = FIBER_OPTIC_LONG_HAUL

def get_config_preset(preset_name: str, raise_error=False, get_default=False) -> ConnectionConfig:
    if preset_name in CONFIG_PRESETS:
        return CONFIG_PRESETS[preset_name]
    elif raise_error:
        raise ValueError(f"Unknown connection preset: {preset_name}")
    elif get_default:
        return DEFAULT_PRESET
    return None
