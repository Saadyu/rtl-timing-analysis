# ============================================================
# ALU 8-bit Timing Constraints
# ============================================================

# Clock
create_clock -name clk -period 2.0 [get_ports clk]

# Input delays
set_input_delay -clock clk 0 [get_ports {a b opcode}]

# Output delays
set_output_delay -clock clk 0 [get_ports {y carry}]