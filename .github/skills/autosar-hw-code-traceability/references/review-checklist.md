# Embedded AUTOSAR review checklist

- MCU ordering code/package and pin mux match confirmed schematic and chip documentation.
- Startup/reset/clock prerequisites and safe output states are correct.
- GPIO/ADC/PWM/communication configurations match the actual external circuit.
- ADC scaling, units, saturation, filtering and diagnostic thresholds have explicit requirements.
- Communication packing, scaling, endianness, timeout, alive counter and CRC match interface specifications where applicable.
- ARXML references, variants, ECUC values, runnable mappings and RTE accesses are consistent.
- State machines cover invalid inputs, reset/recovery and fault priority.
- Task periods, ISR interactions, shared data and timeout behavior are justified.
- DEM/DCM/NvM behavior is requirement-backed.
- Error handling, return values and degraded behavior are appropriate.
- Generated files, generator versions, compiler flags, memory sections and linker/startup artifacts are considered.
- Tests cover normal, boundary, invalid and fault cases; hardware checks are separately tracked.
