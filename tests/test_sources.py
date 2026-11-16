from src.sources import match_resources, FALLBACK_2025


def test_resources_pick_exact_name_not_immatriculations():
    resources = [
        {'title': 'Caract_2024.csv', 'url': 'https://example.org/a.csv'},
        {'title': 'Lieux_2024.csv', 'url': 'https://example.org/b.csv'},
        {'title': 'Vehicules_2024.csv', 'url': 'https://example.org/c.csv'},
        {'title': 'Usagers_2024.csv', 'url': 'https://example.org/d.csv'},
        {'title': 'vehicules-immatricule-baac-2024.csv', 'url': 'https://example.org/ignore.csv'},
    ]
    found = match_resources(resources, [2024])
    assert len(found) == 4
    assert found[(2024, 'vehicules')]['url'].endswith('c.csv')


def test_official_2025_fallbacks_present():
    found = match_resources([], [2025])
    assert len(found) == 4
    for kind in FALLBACK_2025:
        assert '/api/1/datasets/r/' in found[(2025, kind)]['url']
