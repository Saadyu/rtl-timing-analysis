module alu_8 (
    input [7:0] a, b, 
    input [1:0] opcode, 
    input clk, 
    output reg [7:0] y,
    output reg carry
    ); 
    
    reg [7:0] reg_a;
    reg [7:0] reg_b;
    reg [1:0] reg_opcode;
    reg [7:0] reg_y;
    reg reg_carry;


    always_ff @ (posedge clk) begin
        reg_a <= a;
        reg_b <= b;
        reg_opcode <= opcode;
        y <= reg_y;
        carry <= reg_carry;
    end

    always_comb begin
        case (reg_opcode)
            2'b00: begin
                {reg_carry, reg_y} = reg_a + reg_b;
            end

            2'b01: begin
                reg_y = reg_a - reg_b;
                reg_carry = (reg_a < reg_b);    
            end

            2'b10: begin
                reg_y = reg_a & reg_b;
                reg_carry = 0;
            end

            2'b11: begin
                reg_y = reg_a ^ reg_b;
                reg_carry = 0;
            end

            default: begin
                reg_y = 8'b0;
                reg_carry = 1'b0;
            end
        endcase

    end
endmodule