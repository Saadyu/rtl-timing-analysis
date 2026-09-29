module multi_top (
    input  logic       clk,
    input  logic [7:0] a,
    input  logic [7:0] b,
    output logic [7:0] sum
);

    adder u_adder (
        .a(a),
        .b(b),
        .sum(sum)
    );

endmodule