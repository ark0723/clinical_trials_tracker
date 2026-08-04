from app.services.geo import (
    StaticZipGeocoder,
    haversine_miles,
    nearest_site_distance_miles,
    normalize_us_zip,
)


def test_haversine_miles_boston_to_nyc_is_about_190_miles():
    # Boston Common ≈ 42.355, -71.066; NYC Central Park ≈ 40.782, -73.965
    miles = haversine_miles(42.355, -71.066, 40.782, -73.965)
    assert 180 <= miles <= 220


def test_normalize_us_zip_keeps_first_five_digits():
    assert normalize_us_zip("02115-1234") == "02115"
    assert normalize_us_zip("10001") == "10001"
    assert normalize_us_zip("invalid") is None


def test_static_zip_geocoder_returns_known_centroid():
    geocoder = StaticZipGeocoder({"10001": (40.7506, -73.9971)})
    assert geocoder.geocode("10001") == (40.7506, -73.9971)
    assert geocoder.geocode("99999") is None


def test_nearest_site_distance_picks_closest_location():
    origin = (40.7506, -73.9971)  # NYC
    near = (40.7580, -73.9855)  # ~1 mile
    far = (42.3601, -71.0589)  # Boston
    miles = nearest_site_distance_miles(origin, [far, near])
    assert miles is not None
    assert miles < 5
