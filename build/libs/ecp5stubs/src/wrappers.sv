module BBPU_WRAPPER(input I, input T, output O);
    BBPU inner(.I(I), .T(T), .O(O), .B());
endmodule
