# AUTOSAR tracing notes

Trace only artifacts actually present in the project. Names and structures vary by AUTOSAR release and supplier.

Possible layers:
requirement -> schematic net/component/pin -> pin mux/peripheral -> ECUC config -> MCAL -> BSW/IoHwAb -> SWC port/interface/data element -> RTE API/runnable -> OS task/ISR -> test/measurement.

Potential modules include Dio, Adc, Pwm, Port, CanIf, Can, PduR, Com, Dcm, Dem and NvM, but do not assume all exist.

Record ARXML namespace, schema/version, file path, XPath, short name, reference target and variant condition where applicable. XML well-formedness is not equivalent to AUTOSAR schema validation, ECUC consistency validation or successful code generation. Use the project's vendor schemas/tools for authoritative validation. Do not modify generated source directly without identifying its generator inputs.
