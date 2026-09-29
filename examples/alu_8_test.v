module alu_8_test;

    reg [7:0] a;
    reg [7:0] b;
    reg [1:0] opcode;
    reg clk;
    wire [7:0] y;
    wire carry;
    
    alu_8 dut (.a(a), .b(b), .opcode(opcode), .clk(clk), .y(y), .carry(carry));
    initial begin
        $dumpfile("alu_8_test.vcd");
        $dumpvars(0, alu_8_test);
    end

    task display_results;
        $display("Time: %0t | a: %d | b: %d | opcode: %d | y: %d | carry: %b", $time, a, b, opcode, y, carry);
    endtask

    initial begin
        clk = 0;
        forever #5 clk = ~clk;
    end

    initial begin
        // Initial values
        a = 8'h00;
        b = 8'h00;
        opcode = 2'b00;
        display_results;

        // Test 1: ADD
        #12;
        a = 8'h05;
        b = 8'h03;
        opcode = 2'b00;
        display_results;

        // Test 2: ADD with carry
        #10;
        a = 8'hFF;
        b = 8'h01;
        opcode = 2'b00;
        display_results;
        // Test 3: SUB without borrow
        #10;
        a = 8'h08;
        b = 8'h03;
        opcode = 2'b01;
        display_results;

        // Test 4: SUB with borrow
        #10;
        a = 8'h03;
        b = 8'h08;
        opcode = 2'b01;
        display_results;

        // Test 5: AND
        #10;
        a = 8'hF0;
        b = 8'h0F;
        opcode = 2'b10;
        display_results;

        // Test 6: AND
        #10;
        a = 8'hAA;
        b = 8'h55;
        opcode = 2'b10;
        display_results;

        // Test 7: XOR
        #10;
        a = 8'hF0;
        b = 8'h0F;
        opcode = 2'b11;
        display_results;

        // Test 8: XOR
        #10;
        a = 8'hAA;
        b = 8'h55;
        opcode = 2'b11;
        display_results;

        #20;
        $finish;
    end
endmodule

