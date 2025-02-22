"""Test Home Assistant unit conversion utility functions."""
from __future__ import annotations

import inspect

import pytest

from homeassistant.const import (
    UnitOfDataRate,
    UnitOfElectricCurrent,
    UnitOfEnergy,
    UnitOfInformation,
    UnitOfLength,
    UnitOfMass,
    UnitOfPower,
    UnitOfPressure,
    UnitOfSpeed,
    UnitOfTemperature,
    UnitOfVolume,
    UnitOfVolumetricFlux,
)
from homeassistant.exceptions import HomeAssistantError
from homeassistant.util import unit_conversion
from homeassistant.util.unit_conversion import (
    BaseUnitConverter,
    DataRateConverter,
    DistanceConverter,
    ElectricCurrentConverter,
    ElectricPotentialConverter,
    EnergyConverter,
    InformationConverter,
    MassConverter,
    PowerConverter,
    PressureConverter,
    SpeedConverter,
    TemperatureConverter,
    UnitlessRatioConverter,
    VolumeConverter,
)

INVALID_SYMBOL = "bob"


# Dict containing all converters that need to be tested.
# The VALID_UNITS are sorted to ensure that pytest runs are consistent
# and avoid `different tests were collected between gw0 and gw1`
_ALL_CONVERTERS: dict[type[BaseUnitConverter], list[str | None]] = {
    converter: sorted(converter.VALID_UNITS, key=lambda x: (x is None, x))
    for converter in (
        DataRateConverter,
        DistanceConverter,
        ElectricCurrentConverter,
        ElectricPotentialConverter,
        EnergyConverter,
        InformationConverter,
        MassConverter,
        PowerConverter,
        PressureConverter,
        SpeedConverter,
        TemperatureConverter,
        UnitlessRatioConverter,
        VolumeConverter,
    )
}


@pytest.mark.parametrize(
    "converter",
    [
        # Generate list of all converters available in
        # `homeassistant.util.unit_conversion` to ensure
        # that we don't miss any in the tests.
        obj
        for _, obj in inspect.getmembers(unit_conversion)
        if inspect.isclass(obj)
        and issubclass(obj, BaseUnitConverter)
        and obj != BaseUnitConverter
    ],
)
def test_all_converters(converter: type[BaseUnitConverter]) -> None:
    """Ensure all unit converters are tested."""
    assert converter in _ALL_CONVERTERS, "converter is not present in _ALL_CONVERTERS"


@pytest.mark.parametrize(
    "converter,valid_unit",
    [
        # Ensure all units are tested
        (converter, valid_unit)
        for converter, valid_units in _ALL_CONVERTERS.items()
        for valid_unit in valid_units
    ],
)
def test_convert_same_unit(converter: type[BaseUnitConverter], valid_unit: str) -> None:
    """Test conversion from any valid unit to same unit."""
    assert converter.convert(2, valid_unit, valid_unit) == 2


@pytest.mark.parametrize(
    "converter,valid_unit",
    [
        # Ensure all units are tested
        (converter, valid_unit)
        for converter, valid_units in _ALL_CONVERTERS.items()
        for valid_unit in valid_units
    ],
)
def test_convert_invalid_unit(
    converter: type[BaseUnitConverter], valid_unit: str
) -> None:
    """Test exception is thrown for invalid units."""
    with pytest.raises(HomeAssistantError, match="is not a recognized .* unit"):
        converter.convert(5, INVALID_SYMBOL, valid_unit)

    with pytest.raises(HomeAssistantError, match="is not a recognized .* unit"):
        converter.convert(5, valid_unit, INVALID_SYMBOL)


@pytest.mark.parametrize(
    "converter,from_unit,to_unit",
    [
        # Pick any two units
        (converter, valid_units[0], valid_units[1])
        for converter, valid_units in _ALL_CONVERTERS.items()
    ],
)
def test_convert_nonnumeric_value(
    converter: type[BaseUnitConverter], from_unit: str, to_unit: str
) -> None:
    """Test exception is thrown for nonnumeric type."""
    with pytest.raises(TypeError):
        converter.convert("a", from_unit, to_unit)


@pytest.mark.parametrize(
    "converter,from_unit,to_unit,expected",
    [
        (
            DataRateConverter,
            UnitOfDataRate.BITS_PER_SECOND,
            UnitOfDataRate.BYTES_PER_SECOND,
            8,
        ),
        (DistanceConverter, UnitOfLength.KILOMETERS, UnitOfLength.METERS, 1 / 1000),
        (
            ElectricCurrentConverter,
            UnitOfElectricCurrent.AMPERE,
            UnitOfElectricCurrent.MILLIAMPERE,
            1 / 1000,
        ),
        (EnergyConverter, UnitOfEnergy.WATT_HOUR, UnitOfEnergy.KILO_WATT_HOUR, 1000),
        (InformationConverter, UnitOfInformation.BITS, UnitOfInformation.BYTES, 8),
        (PowerConverter, UnitOfPower.WATT, UnitOfPower.KILO_WATT, 1000),
        (
            PressureConverter,
            UnitOfPressure.HPA,
            UnitOfPressure.INHG,
            pytest.approx(33.86389),
        ),
        (
            SpeedConverter,
            UnitOfSpeed.KILOMETERS_PER_HOUR,
            UnitOfSpeed.MILES_PER_HOUR,
            pytest.approx(1.609343),
        ),
        (
            TemperatureConverter,
            UnitOfTemperature.CELSIUS,
            UnitOfTemperature.FAHRENHEIT,
            1 / 1.8,
        ),
        (
            VolumeConverter,
            UnitOfVolume.GALLONS,
            UnitOfVolume.LITERS,
            pytest.approx(0.264172),
        ),
    ],
)
def test_get_unit_ratio(
    converter: type[BaseUnitConverter], from_unit: str, to_unit: str, expected: float
) -> None:
    """Test unit ratio."""
    assert converter.get_unit_ratio(from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (8e3, UnitOfDataRate.BITS_PER_SECOND, 8, UnitOfDataRate.KILOBITS_PER_SECOND),
        (8e6, UnitOfDataRate.BITS_PER_SECOND, 8, UnitOfDataRate.MEGABITS_PER_SECOND),
        (8e9, UnitOfDataRate.BITS_PER_SECOND, 8, UnitOfDataRate.GIGABITS_PER_SECOND),
        (8, UnitOfDataRate.BITS_PER_SECOND, 1, UnitOfDataRate.BYTES_PER_SECOND),
        (8e3, UnitOfDataRate.BITS_PER_SECOND, 1, UnitOfDataRate.KILOBYTES_PER_SECOND),
        (8e6, UnitOfDataRate.BITS_PER_SECOND, 1, UnitOfDataRate.MEGABYTES_PER_SECOND),
        (8e9, UnitOfDataRate.BITS_PER_SECOND, 1, UnitOfDataRate.GIGABYTES_PER_SECOND),
        (
            8 * 2**10,
            UnitOfDataRate.BITS_PER_SECOND,
            1,
            UnitOfDataRate.KIBIBYTES_PER_SECOND,
        ),
        (
            8 * 2**20,
            UnitOfDataRate.BITS_PER_SECOND,
            1,
            UnitOfDataRate.MEBIBYTES_PER_SECOND,
        ),
        (
            8 * 2**30,
            UnitOfDataRate.BITS_PER_SECOND,
            1,
            UnitOfDataRate.GIBIBYTES_PER_SECOND,
        ),
    ],
)
def test_data_rate_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert DataRateConverter.convert(value, from_unit, to_unit) == pytest.approx(
        expected
    )


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (5, UnitOfElectricCurrent.AMPERE, 5000, UnitOfElectricCurrent.MILLIAMPERE),
        (5, UnitOfElectricCurrent.MILLIAMPERE, 0.005, UnitOfElectricCurrent.AMPERE),
    ],
)
def test_electric_current_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert ElectricCurrentConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (5, UnitOfLength.MILES, 8.04672, UnitOfLength.KILOMETERS),
        (5, UnitOfLength.MILES, 8046.72, UnitOfLength.METERS),
        (5, UnitOfLength.MILES, 804672.0, UnitOfLength.CENTIMETERS),
        (5, UnitOfLength.MILES, 8046720.0, UnitOfLength.MILLIMETERS),
        (5, UnitOfLength.MILES, 8800.0, UnitOfLength.YARDS),
        (5, UnitOfLength.MILES, 26400.0008448, UnitOfLength.FEET),
        (5, UnitOfLength.MILES, 316800.171072, UnitOfLength.INCHES),
        (5, UnitOfLength.YARDS, 0.004572, UnitOfLength.KILOMETERS),
        (5, UnitOfLength.YARDS, 4.572, UnitOfLength.METERS),
        (5, UnitOfLength.YARDS, 457.2, UnitOfLength.CENTIMETERS),
        (5, UnitOfLength.YARDS, 4572, UnitOfLength.MILLIMETERS),
        (5, UnitOfLength.YARDS, 0.002840908212, UnitOfLength.MILES),
        (5, UnitOfLength.YARDS, 15.00000048, UnitOfLength.FEET),
        (5, UnitOfLength.YARDS, 180.0000972, UnitOfLength.INCHES),
        (5000, UnitOfLength.FEET, 1.524, UnitOfLength.KILOMETERS),
        (5000, UnitOfLength.FEET, 1524, UnitOfLength.METERS),
        (5000, UnitOfLength.FEET, 152400.0, UnitOfLength.CENTIMETERS),
        (5000, UnitOfLength.FEET, 1524000.0, UnitOfLength.MILLIMETERS),
        (5000, UnitOfLength.FEET, 0.946969404, UnitOfLength.MILES),
        (5000, UnitOfLength.FEET, 1666.66667, UnitOfLength.YARDS),
        (5000, UnitOfLength.FEET, 60000.0324, UnitOfLength.INCHES),
        (5000, UnitOfLength.INCHES, 0.127, UnitOfLength.KILOMETERS),
        (5000, UnitOfLength.INCHES, 127.0, UnitOfLength.METERS),
        (5000, UnitOfLength.INCHES, 12700.0, UnitOfLength.CENTIMETERS),
        (5000, UnitOfLength.INCHES, 127000.0, UnitOfLength.MILLIMETERS),
        (5000, UnitOfLength.INCHES, 0.078914117, UnitOfLength.MILES),
        (5000, UnitOfLength.INCHES, 138.88889, UnitOfLength.YARDS),
        (5000, UnitOfLength.INCHES, 416.66668, UnitOfLength.FEET),
        (5, UnitOfLength.KILOMETERS, 5000, UnitOfLength.METERS),
        (5, UnitOfLength.KILOMETERS, 500000, UnitOfLength.CENTIMETERS),
        (5, UnitOfLength.KILOMETERS, 5000000, UnitOfLength.MILLIMETERS),
        (5, UnitOfLength.KILOMETERS, 3.106855, UnitOfLength.MILES),
        (5, UnitOfLength.KILOMETERS, 5468.066, UnitOfLength.YARDS),
        (5, UnitOfLength.KILOMETERS, 16404.2, UnitOfLength.FEET),
        (5, UnitOfLength.KILOMETERS, 196850.5, UnitOfLength.INCHES),
        (5000, UnitOfLength.METERS, 5, UnitOfLength.KILOMETERS),
        (5000, UnitOfLength.METERS, 500000, UnitOfLength.CENTIMETERS),
        (5000, UnitOfLength.METERS, 5000000, UnitOfLength.MILLIMETERS),
        (5000, UnitOfLength.METERS, 3.106855, UnitOfLength.MILES),
        (5000, UnitOfLength.METERS, 5468.066, UnitOfLength.YARDS),
        (5000, UnitOfLength.METERS, 16404.2, UnitOfLength.FEET),
        (5000, UnitOfLength.METERS, 196850.5, UnitOfLength.INCHES),
        (500000, UnitOfLength.CENTIMETERS, 5, UnitOfLength.KILOMETERS),
        (500000, UnitOfLength.CENTIMETERS, 5000, UnitOfLength.METERS),
        (500000, UnitOfLength.CENTIMETERS, 5000000, UnitOfLength.MILLIMETERS),
        (500000, UnitOfLength.CENTIMETERS, 3.106855, UnitOfLength.MILES),
        (500000, UnitOfLength.CENTIMETERS, 5468.066, UnitOfLength.YARDS),
        (500000, UnitOfLength.CENTIMETERS, 16404.2, UnitOfLength.FEET),
        (500000, UnitOfLength.CENTIMETERS, 196850.5, UnitOfLength.INCHES),
        (5000000, UnitOfLength.MILLIMETERS, 5, UnitOfLength.KILOMETERS),
        (5000000, UnitOfLength.MILLIMETERS, 5000, UnitOfLength.METERS),
        (5000000, UnitOfLength.MILLIMETERS, 500000, UnitOfLength.CENTIMETERS),
        (5000000, UnitOfLength.MILLIMETERS, 3.106855, UnitOfLength.MILES),
        (5000000, UnitOfLength.MILLIMETERS, 5468.066, UnitOfLength.YARDS),
        (5000000, UnitOfLength.MILLIMETERS, 16404.2, UnitOfLength.FEET),
        (5000000, UnitOfLength.MILLIMETERS, 196850.5, UnitOfLength.INCHES),
    ],
)
def test_distance_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    expected = pytest.approx(expected)
    assert DistanceConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (10, UnitOfEnergy.WATT_HOUR, 0.01, UnitOfEnergy.KILO_WATT_HOUR),
        (10, UnitOfEnergy.WATT_HOUR, 0.00001, UnitOfEnergy.MEGA_WATT_HOUR),
        (10, UnitOfEnergy.KILO_WATT_HOUR, 10000, UnitOfEnergy.WATT_HOUR),
        (10, UnitOfEnergy.KILO_WATT_HOUR, 0.01, UnitOfEnergy.MEGA_WATT_HOUR),
        (10, UnitOfEnergy.MEGA_WATT_HOUR, 10000000, UnitOfEnergy.WATT_HOUR),
        (10, UnitOfEnergy.MEGA_WATT_HOUR, 10000, UnitOfEnergy.KILO_WATT_HOUR),
        (10, UnitOfEnergy.GIGA_JOULE, 10000 / 3.6, UnitOfEnergy.KILO_WATT_HOUR),
        (10, UnitOfEnergy.GIGA_JOULE, 10 / 3.6, UnitOfEnergy.MEGA_WATT_HOUR),
    ],
)
def test_energy_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert EnergyConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (8e3, UnitOfInformation.BITS, 8, UnitOfInformation.KILOBITS),
        (8e6, UnitOfInformation.BITS, 8, UnitOfInformation.MEGABITS),
        (8e9, UnitOfInformation.BITS, 8, UnitOfInformation.GIGABITS),
        (8, UnitOfInformation.BITS, 1, UnitOfInformation.BYTES),
        (8e3, UnitOfInformation.BITS, 1, UnitOfInformation.KILOBYTES),
        (8e6, UnitOfInformation.BITS, 1, UnitOfInformation.MEGABYTES),
        (8e9, UnitOfInformation.BITS, 1, UnitOfInformation.GIGABYTES),
        (8e12, UnitOfInformation.BITS, 1, UnitOfInformation.TERABYTES),
        (8e15, UnitOfInformation.BITS, 1, UnitOfInformation.PETABYTES),
        (8e18, UnitOfInformation.BITS, 1, UnitOfInformation.EXABYTES),
        (8e21, UnitOfInformation.BITS, 1, UnitOfInformation.ZETTABYTES),
        (8e24, UnitOfInformation.BITS, 1, UnitOfInformation.YOTTABYTES),
        (8 * 2**10, UnitOfInformation.BITS, 1, UnitOfInformation.KIBIBYTES),
        (8 * 2**20, UnitOfInformation.BITS, 1, UnitOfInformation.MEBIBYTES),
        (8 * 2**30, UnitOfInformation.BITS, 1, UnitOfInformation.GIBIBYTES),
        (8 * 2**40, UnitOfInformation.BITS, 1, UnitOfInformation.TEBIBYTES),
        (8 * 2**50, UnitOfInformation.BITS, 1, UnitOfInformation.PEBIBYTES),
        (8 * 2**60, UnitOfInformation.BITS, 1, UnitOfInformation.EXBIBYTES),
        (8 * 2**70, UnitOfInformation.BITS, 1, UnitOfInformation.ZEBIBYTES),
        (8 * 2**80, UnitOfInformation.BITS, 1, UnitOfInformation.YOBIBYTES),
    ],
)
def test_information_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    expected = pytest.approx(expected)
    assert InformationConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (10, UnitOfMass.KILOGRAMS, 10000, UnitOfMass.GRAMS),
        (10, UnitOfMass.KILOGRAMS, 10000000, UnitOfMass.MILLIGRAMS),
        (10, UnitOfMass.KILOGRAMS, 10000000000, UnitOfMass.MICROGRAMS),
        (10, UnitOfMass.KILOGRAMS, 352.73961, UnitOfMass.OUNCES),
        (10, UnitOfMass.KILOGRAMS, 22.046226, UnitOfMass.POUNDS),
        (10, UnitOfMass.GRAMS, 0.01, UnitOfMass.KILOGRAMS),
        (10, UnitOfMass.GRAMS, 10000, UnitOfMass.MILLIGRAMS),
        (10, UnitOfMass.GRAMS, 10000000, UnitOfMass.MICROGRAMS),
        (10, UnitOfMass.GRAMS, 0.35273961, UnitOfMass.OUNCES),
        (10, UnitOfMass.GRAMS, 0.022046226, UnitOfMass.POUNDS),
        (10, UnitOfMass.MILLIGRAMS, 0.00001, UnitOfMass.KILOGRAMS),
        (10, UnitOfMass.MILLIGRAMS, 0.01, UnitOfMass.GRAMS),
        (10, UnitOfMass.MILLIGRAMS, 10000, UnitOfMass.MICROGRAMS),
        (10, UnitOfMass.MILLIGRAMS, 0.00035273961, UnitOfMass.OUNCES),
        (10, UnitOfMass.MILLIGRAMS, 0.000022046226, UnitOfMass.POUNDS),
        (10000, UnitOfMass.MICROGRAMS, 0.00001, UnitOfMass.KILOGRAMS),
        (10000, UnitOfMass.MICROGRAMS, 0.01, UnitOfMass.GRAMS),
        (10000, UnitOfMass.MICROGRAMS, 10, UnitOfMass.MILLIGRAMS),
        (10000, UnitOfMass.MICROGRAMS, 0.00035273961, UnitOfMass.OUNCES),
        (10000, UnitOfMass.MICROGRAMS, 0.000022046226, UnitOfMass.POUNDS),
        (1, UnitOfMass.POUNDS, 0.45359237, UnitOfMass.KILOGRAMS),
        (1, UnitOfMass.POUNDS, 453.59237, UnitOfMass.GRAMS),
        (1, UnitOfMass.POUNDS, 453592.37, UnitOfMass.MILLIGRAMS),
        (1, UnitOfMass.POUNDS, 453592370, UnitOfMass.MICROGRAMS),
        (1, UnitOfMass.POUNDS, 16, UnitOfMass.OUNCES),
        (16, UnitOfMass.OUNCES, 0.45359237, UnitOfMass.KILOGRAMS),
        (16, UnitOfMass.OUNCES, 453.59237, UnitOfMass.GRAMS),
        (16, UnitOfMass.OUNCES, 453592.37, UnitOfMass.MILLIGRAMS),
        (16, UnitOfMass.OUNCES, 453592370, UnitOfMass.MICROGRAMS),
        (16, UnitOfMass.OUNCES, 1, UnitOfMass.POUNDS),
        (1, UnitOfMass.STONES, 6.350293, UnitOfMass.KILOGRAMS),
        (1, UnitOfMass.STONES, 6350.293, UnitOfMass.GRAMS),
        (1, UnitOfMass.STONES, 6350293, UnitOfMass.MILLIGRAMS),
        (1, UnitOfMass.STONES, 14, UnitOfMass.POUNDS),
        (1, UnitOfMass.STONES, 224, UnitOfMass.OUNCES),
    ],
)
def test_mass_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert MassConverter.convert(value, from_unit, to_unit) == pytest.approx(expected)


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (10, UnitOfPower.KILO_WATT, 10000, UnitOfPower.WATT),
        (10, UnitOfPower.WATT, 0.01, UnitOfPower.KILO_WATT),
    ],
)
def test_power_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert PowerConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (1000, UnitOfPressure.HPA, 14.5037743897, UnitOfPressure.PSI),
        (1000, UnitOfPressure.HPA, 29.5299801647, UnitOfPressure.INHG),
        (1000, UnitOfPressure.HPA, 100000, UnitOfPressure.PA),
        (1000, UnitOfPressure.HPA, 100, UnitOfPressure.KPA),
        (1000, UnitOfPressure.HPA, 1000, UnitOfPressure.MBAR),
        (1000, UnitOfPressure.HPA, 100, UnitOfPressure.CBAR),
        (100, UnitOfPressure.KPA, 14.5037743897, UnitOfPressure.PSI),
        (100, UnitOfPressure.KPA, 29.5299801647, UnitOfPressure.INHG),
        (100, UnitOfPressure.KPA, 100000, UnitOfPressure.PA),
        (100, UnitOfPressure.KPA, 1000, UnitOfPressure.HPA),
        (100, UnitOfPressure.KPA, 1000, UnitOfPressure.MBAR),
        (100, UnitOfPressure.KPA, 100, UnitOfPressure.CBAR),
        (30, UnitOfPressure.INHG, 14.7346266155, UnitOfPressure.PSI),
        (30, UnitOfPressure.INHG, 101.59167, UnitOfPressure.KPA),
        (30, UnitOfPressure.INHG, 1015.9167, UnitOfPressure.HPA),
        (30, UnitOfPressure.INHG, 101591.67, UnitOfPressure.PA),
        (30, UnitOfPressure.INHG, 1015.9167, UnitOfPressure.MBAR),
        (30, UnitOfPressure.INHG, 101.59167, UnitOfPressure.CBAR),
        (30, UnitOfPressure.INHG, 762, UnitOfPressure.MMHG),
        (30, UnitOfPressure.MMHG, 0.580103, UnitOfPressure.PSI),
        (30, UnitOfPressure.MMHG, 3.99967, UnitOfPressure.KPA),
        (30, UnitOfPressure.MMHG, 39.9967, UnitOfPressure.HPA),
        (30, UnitOfPressure.MMHG, 3999.67, UnitOfPressure.PA),
        (30, UnitOfPressure.MMHG, 39.9967, UnitOfPressure.MBAR),
        (30, UnitOfPressure.MMHG, 3.99967, UnitOfPressure.CBAR),
        (30, UnitOfPressure.MMHG, 1.181102, UnitOfPressure.INHG),
    ],
)
def test_pressure_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    expected = pytest.approx(expected)
    assert PressureConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        # 5 km/h / 1.609 km/mi = 3.10686 mi/h
        (5, UnitOfSpeed.KILOMETERS_PER_HOUR, 3.106856, UnitOfSpeed.MILES_PER_HOUR),
        # 5 mi/h * 1.609 km/mi = 8.04672 km/h
        (5, UnitOfSpeed.MILES_PER_HOUR, 8.04672, UnitOfSpeed.KILOMETERS_PER_HOUR),
        # 5 in/day * 25.4 mm/in = 127 mm/day
        (
            5,
            UnitOfVolumetricFlux.INCHES_PER_DAY,
            127,
            UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        ),
        # 5 mm/day / 25.4 mm/in = 0.19685 in/day
        (
            5,
            UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
            0.1968504,
            UnitOfVolumetricFlux.INCHES_PER_DAY,
        ),
        # 48 mm/day = 2 mm/h
        (
            48,
            UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
            2,
            UnitOfVolumetricFlux.MILLIMETERS_PER_HOUR,
        ),
        # 5 in/hr * 24 hr/day = 3048 mm/day
        (
            5,
            UnitOfVolumetricFlux.INCHES_PER_HOUR,
            3048,
            UnitOfVolumetricFlux.MILLIMETERS_PER_DAY,
        ),
        # 5 m/s * 39.3701 in/m * 3600 s/hr = 708661
        (
            5,
            UnitOfSpeed.METERS_PER_SECOND,
            708661.42,
            UnitOfVolumetricFlux.INCHES_PER_HOUR,
        ),
        # 5000 in/h / 39.3701 in/m / 3600 s/h = 0.03528 m/s
        (
            5000,
            UnitOfVolumetricFlux.INCHES_PER_HOUR,
            0.0352778,
            UnitOfSpeed.METERS_PER_SECOND,
        ),
        # 5 kt * 1852 m/nmi / 3600 s/h = 2.5722 m/s
        (5, UnitOfSpeed.KNOTS, 2.57222, UnitOfSpeed.METERS_PER_SECOND),
        # 5 ft/s * 0.3048 m/ft = 1.524 m/s
        (5, UnitOfSpeed.FEET_PER_SECOND, 1.524, UnitOfSpeed.METERS_PER_SECOND),
    ],
)
def test_speed_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert SpeedConverter.convert(value, from_unit, to_unit) == pytest.approx(expected)


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (100, UnitOfTemperature.CELSIUS, 212, UnitOfTemperature.FAHRENHEIT),
        (100, UnitOfTemperature.CELSIUS, 373.15, UnitOfTemperature.KELVIN),
        (100, UnitOfTemperature.FAHRENHEIT, 37.7778, UnitOfTemperature.CELSIUS),
        (100, UnitOfTemperature.FAHRENHEIT, 310.9277, UnitOfTemperature.KELVIN),
        (100, UnitOfTemperature.KELVIN, -173.15, UnitOfTemperature.CELSIUS),
        (100, UnitOfTemperature.KELVIN, -279.6699, UnitOfTemperature.FAHRENHEIT),
    ],
)
def test_temperature_convert(
    value: float, from_unit: str, expected: float, to_unit: str
) -> None:
    """Test conversion to other units."""
    expected = pytest.approx(expected)
    assert TemperatureConverter.convert(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (100, UnitOfTemperature.CELSIUS, 180, UnitOfTemperature.FAHRENHEIT),
        (100, UnitOfTemperature.CELSIUS, 100, UnitOfTemperature.KELVIN),
        (100, UnitOfTemperature.FAHRENHEIT, 55.5556, UnitOfTemperature.CELSIUS),
        (100, UnitOfTemperature.FAHRENHEIT, 55.5556, UnitOfTemperature.KELVIN),
        (100, UnitOfTemperature.KELVIN, 100, UnitOfTemperature.CELSIUS),
        (100, UnitOfTemperature.KELVIN, 180, UnitOfTemperature.FAHRENHEIT),
    ],
)
def test_temperature_convert_with_interval(
    value: float, from_unit: str, expected: float, to_unit: str
) -> None:
    """Test conversion to other units."""
    expected = pytest.approx(expected)
    assert TemperatureConverter.convert_interval(value, from_unit, to_unit) == expected


@pytest.mark.parametrize(
    "value,from_unit,expected,to_unit",
    [
        (5, UnitOfVolume.LITERS, 1.32086, UnitOfVolume.GALLONS),
        (5, UnitOfVolume.GALLONS, 18.92706, UnitOfVolume.LITERS),
        (5, UnitOfVolume.CUBIC_METERS, 176.5733335, UnitOfVolume.CUBIC_FEET),
        (500, UnitOfVolume.CUBIC_FEET, 14.1584233, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.CUBIC_FEET, 14.1584233, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.CUBIC_FEET, 478753.2467, UnitOfVolume.FLUID_OUNCES),
        (500, UnitOfVolume.CUBIC_FEET, 3740.25974, UnitOfVolume.GALLONS),
        (500, UnitOfVolume.CUBIC_FEET, 14158.42329599, UnitOfVolume.LITERS),
        (500, UnitOfVolume.CUBIC_FEET, 14158423.29599, UnitOfVolume.MILLILITERS),
        (500, UnitOfVolume.CUBIC_METERS, 500, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.CUBIC_METERS, 16907011.35, UnitOfVolume.FLUID_OUNCES),
        (500, UnitOfVolume.CUBIC_METERS, 132086.02617, UnitOfVolume.GALLONS),
        (500, UnitOfVolume.CUBIC_METERS, 500000, UnitOfVolume.LITERS),
        (500, UnitOfVolume.CUBIC_METERS, 500000000, UnitOfVolume.MILLILITERS),
        (500, UnitOfVolume.FLUID_OUNCES, 0.52218967, UnitOfVolume.CUBIC_FEET),
        (500, UnitOfVolume.FLUID_OUNCES, 0.014786764, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.FLUID_OUNCES, 3.90625, UnitOfVolume.GALLONS),
        (500, UnitOfVolume.FLUID_OUNCES, 14.786764, UnitOfVolume.LITERS),
        (500, UnitOfVolume.FLUID_OUNCES, 14786.764, UnitOfVolume.MILLILITERS),
        (500, UnitOfVolume.GALLONS, 66.84027, UnitOfVolume.CUBIC_FEET),
        (500, UnitOfVolume.GALLONS, 1.892706, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.GALLONS, 64000, UnitOfVolume.FLUID_OUNCES),
        (500, UnitOfVolume.GALLONS, 1892.70589, UnitOfVolume.LITERS),
        (500, UnitOfVolume.GALLONS, 1892705.89, UnitOfVolume.MILLILITERS),
        (500, UnitOfVolume.LITERS, 17.65733, UnitOfVolume.CUBIC_FEET),
        (500, UnitOfVolume.LITERS, 0.5, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.LITERS, 16907.011, UnitOfVolume.FLUID_OUNCES),
        (500, UnitOfVolume.LITERS, 132.086, UnitOfVolume.GALLONS),
        (500, UnitOfVolume.LITERS, 500000, UnitOfVolume.MILLILITERS),
        (500, UnitOfVolume.MILLILITERS, 0.01765733, UnitOfVolume.CUBIC_FEET),
        (500, UnitOfVolume.MILLILITERS, 0.0005, UnitOfVolume.CUBIC_METERS),
        (500, UnitOfVolume.MILLILITERS, 16.907, UnitOfVolume.FLUID_OUNCES),
        (500, UnitOfVolume.MILLILITERS, 0.132086, UnitOfVolume.GALLONS),
        (500, UnitOfVolume.MILLILITERS, 0.5, UnitOfVolume.LITERS),
        (5, UnitOfVolume.CENTUM_CUBIC_FEET, 500, UnitOfVolume.CUBIC_FEET),
        (5, UnitOfVolume.CENTUM_CUBIC_FEET, 14.15842, UnitOfVolume.CUBIC_METERS),
        (5, UnitOfVolume.CENTUM_CUBIC_FEET, 478753.24, UnitOfVolume.FLUID_OUNCES),
        (5, UnitOfVolume.CENTUM_CUBIC_FEET, 3740.26, UnitOfVolume.GALLONS),
        (5, UnitOfVolume.CENTUM_CUBIC_FEET, 14158.42, UnitOfVolume.LITERS),
    ],
)
def test_volume_convert(
    value: float,
    from_unit: str,
    expected: float,
    to_unit: str,
) -> None:
    """Test conversion to other units."""
    assert VolumeConverter.convert(value, from_unit, to_unit) == pytest.approx(expected)
