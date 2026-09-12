package dev.drewcraft.service.vehicle;

import java.util.List;
import java.util.Objects;

public record VehicleQueryResult(
        boolean available,
        String providerId,
        List<VehicleSnapshot> vehicles,
        String status
) {
    public VehicleQueryResult {
        Objects.requireNonNull(providerId);
        vehicles = List.copyOf(vehicles);
        Objects.requireNonNull(status);
    }

    public static VehicleQueryResult unavailable(String providerId, String status) {
        return new VehicleQueryResult(false, providerId, List.of(), status);
    }
}
