{
  tris_logic : {
    c0(default: "") -> tris_logic.c0;
    c1(default: "") -> tris_logic.c1;
    c2(default: "") -> tris_logic.c2;
    c3(default: "") -> tris_logic.c3;
    c4(default: "") -> tris_logic.c4;
    c5(default: "") -> tris_logic.c5;
    c6(default: "") -> tris_logic.c6;
    c7(default: "") -> tris_logic.c7;
    c8(default: "") -> tris_logic.c8;

    turn(default: "O") -> tris_logic.turn;
    
    play_0(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c0", payload: tris_logic.c0 == "" and tris_logic.turn or tris_logic.c0),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_1(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c1", payload: tris_logic.c1 == "" and tris_logic.turn or tris_logic.c1),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_2(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c2", payload: tris_logic.c2 == "" and tris_logic.turn or tris_logic.c2),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_3(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c3", payload: tris_logic.c3 == "" and tris_logic.turn or tris_logic.c3),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_4(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c4", payload: tris_logic.c4 == "" and tris_logic.turn or tris_logic.c4),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_5(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c5", payload: tris_logic.c5 == "" and tris_logic.turn or tris_logic.c5),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_6(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c6", payload: tris_logic.c6 == "" and tris_logic.turn or tris_logic.c6),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_7(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c7", payload: tris_logic.c7 == "" and tris_logic.turn or tris_logic.c7),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];
    play_8(deps:false, on_success: "tris_logic.check_victory") -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c8", payload: tris_logic.c8 == "" and tris_logic.turn or tris_logic.c8),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X") )
    ];

    winner(default: "") -> tris_logic.winner;

    check_victory() -> {
        c0: tris_logic.c0;
        c1: tris_logic.c1;
        c2: tris_logic.c2;
        c3: tris_logic.c3;
        c4: tris_logic.c4;
        c5: tris_logic.c5;
        c6: tris_logic.c6;
        c7: tris_logic.c7;
        c8: tris_logic.c8;
        winner: tris_logic.winner;
    } |> switch({
        @c0 != "" & @winner == "" & @c0 == @c3 & @c3 == @c6: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c1 != "" & @winner == "" & @c1 == @c4 & @c4 == @c7: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c2 != "" & @winner == "" & @c2 == @c5 & @c5 == @c8: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c0 != "" & @winner == "" & @c0 == @c4 & @c4 == @c8: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c2 != "" & @winner == "" & @c2 == @c4 & @c4 == @c6: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c0 != "" & @winner == "" & @c0 == @c1 & @c1 == @c2: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c3 != "" & @winner == "" & @c3 == @c4 & @c4 == @c5: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
        @c6 != "" & @winner == "" & @c6 == @c7 & @c7 == @c8: @messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: (tris_logic.turn == "X" and "O") or (tris_logic.turn == "O" and "X"));
    });

    reset_btn(deps:false) -> [
        messenger.send(session: sid, domain: "tris:tris_logic.c0", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c1", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c2", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c3", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c4", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c5", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c6", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c7", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.c8", payload: ""),
        messenger.send(session: sid, domain: "tris:tris_logic.turn", payload: "X"),
        messenger.send(session: sid, domain: "tris:tris_logic.winner", payload: "")
    ];
  }
}
