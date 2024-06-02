from spade import Spade

def init(uut: str, state_path: str) -> Spade:
    print("Running init")
    return Spade(uut, state_path)

def translate(s: Spade, hierarchy: str, value: int | str):
    if isinstance(value, int):
        value = f"{value:b}"

    return s.translate_value(hierarchy, value)


if __name__ == "__main__":
    s = init("proj::test::axi_read_test::read_harness", "../build/state.ron")

    print(s.translate_value("axi_single_read_0.state", "00xxxxxxxxxxxxxxxxxxxxxxxx"))
