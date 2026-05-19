import folium
from folium import plugins

from viewtrip.core.models import Journey


def render_journey_map(journey: Journey) -> str:
    coords: list[tuple[float, float]] = []
    for leg in journey.legs:
        coords.extend(leg.stop_coords)

    if not coords:
        return ""

    center = (
        sum(c[0] for c in coords) / len(coords),
        sum(c[1] for c in coords) / len(coords),
    )
    m = folium.Map(location=center, zoom_start=12)

    seen: set[tuple[float, float]] = set()
    for leg in journey.legs:
        for coord in leg.stop_coords:
            if coord in seen:
                continue
            seen.add(coord)
            folium.Marker(location=coord).add_to(m)

    plugins.AntPath(locations=coords, color="blue").add_to(m)
    return m.get_root().render()
