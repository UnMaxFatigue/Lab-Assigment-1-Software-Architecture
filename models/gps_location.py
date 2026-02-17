class GPSLocation:
    latitude: float
    longitude: float

    def __init__(self, latitude: float, longitude: float) -> None:
        if not -90 <= latitude <= 90:
            raise ValueError(f"Invalid latitude {latitude}. Must be between -90 and 90.")
        if not -180 <= longitude <= 180:
            raise ValueError(f"Invalid longitude {longitude}. Must be between -180 and 180.")
        self.latitude = latitude
        self.longitude = longitude
