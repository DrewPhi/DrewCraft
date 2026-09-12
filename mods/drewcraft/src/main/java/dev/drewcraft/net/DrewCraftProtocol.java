package dev.drewcraft.net;

public final class DrewCraftProtocol {
    public static final Version CURRENT_VERSION = new Version(1, 0);
    public static final String CURRENT = CURRENT_VERSION.toString();

    private DrewCraftProtocol() {
    }

    public static boolean isCompatible(String remoteVersion) {
        try {
            return CURRENT_VERSION.major() == Version.parse(remoteVersion).major();
        } catch (IllegalArgumentException exception) {
            return false;
        }
    }

    public record Version(int major, int minor) {
        public Version {
            if (major < 0 || minor < 0) {
                throw new IllegalArgumentException("Protocol components must be non-negative");
            }
        }

        public static Version parse(String value) {
            if (value == null) {
                throw new IllegalArgumentException("Protocol version is null");
            }
            String[] parts = value.split("\\.", -1);
            if (parts.length != 2 || parts[0].isBlank() || parts[1].isBlank()) {
                throw new IllegalArgumentException("Protocol version must be MAJOR.MINOR");
            }
            try {
                return new Version(Integer.parseInt(parts[0]), Integer.parseInt(parts[1]));
            } catch (NumberFormatException exception) {
                throw new IllegalArgumentException("Protocol version must be numeric", exception);
            }
        }

        @Override
        public String toString() {
            return major + "." + minor;
        }
    }
}
