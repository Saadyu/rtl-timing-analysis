create_clock -name clk -period 5.0 [get_ports clk]

set_input_delay -clock clk 0 [get_ports {a b}]
set_output_delay -clock clk 0 [get_ports sum]