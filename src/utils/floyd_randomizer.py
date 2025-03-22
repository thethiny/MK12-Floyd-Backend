from typing import List
import cityhash


def concat(a: int, b: int):
    return ((a & 0xFFFFFFFF) << 32) | (b & 0xFFFFFFFF)


def convert_profile_id_to_seed(profile_id_string: str):
    string = profile_id_string.encode("utf-16-le")
    hash = cityhash.CityHash64(string)

    hash_lo = hash & 0xFFFFFFFF
    hash_hi = (hash >> 0x20) & 0xFFFFFFFF
    hash = ((hash_hi * 0x17) & 0xFFFFFFFF) + hash_lo
    return hash & 0xFFFFFFFF


def do_stuff_with_seed(floyd_init: int, floyd_encounters: int):
    seed_2_0 = 0x280AF6FDEECF029F
    seed_2_1 = seed_2_0
    mask_64 = 0xFFFFFFFFFFFFFFFF
    floyd_seed = concat(floyd_init, floyd_encounters)
    result = seed_2_0

    seed_0 = 0x5851F42D4C957F2D
    seed_0 *= (result + floyd_seed) & mask_64
    seed_0 &= mask_64
    seed_0 += result
    seed_0 &= mask_64

    neg_a1 = ~floyd_seed
    neg_a1 &= mask_64

    _add = (seed_2_1 + neg_a1) & mask_64
    _mul = _add * 0x5851F42D4C957F2D
    _mul &= mask_64
    seed_1 = seed_2_1 + _mul
    seed_1 &= mask_64

    return seed_1, seed_2_1


def shuffler(array: List[int], seed_1: int, seed_2: int):
    length = len(array)
    for v15 in range(length):
        v4 = seed_2
        v5 = (-length & 0xFFFFFFFF) % length
        v8 = v5 - 1  # This is only to enable the while loop
        while v8 < v5:
            v6 = seed_1
            v7 = seed_1 >> 45
            seed_1 = 0x5851F42D4C957F2D * seed_1
            seed_1 &= 0xFFFFFFFFFFFFFFFF
            seed_1 += v4
            seed_1 &= 0xFFFFFFFFFFFFFFFF
            xor_v = ((v6 >> 27) ^ v7) & 0xFFFFFFFF
            shift_amt = (
                -(v6 >> 59) & 0x1F
            ) & 0xFFFFFFFFFFFFFFFF  # I think something is wrong here
            left_shift = xor_v << (
                shift_amt & 0xFFFFFFFF
            )  # the shift_amt is int64 but xor_v is int32 and we can't afford overflow
            left_shift &= 0xFFFFFFFF

            l_right_shift = v6 >> 59
            v8 = (xor_v >> l_right_shift) | left_shift
            v8 &= 0xFFFFFFFF
        index = v8 % length
        index += v15
        length -= 1
        if index != v15:  # Shuffle if it's not this index
            v20 = array[index]
            v21 = v20
            array[index] = array[v15]
            array[v15] = v21


if __name__ == "__main__":
    array = list(range(37))

    string = "PLATFORM:PLATFORM_ID/MK_ACCOUNT_ID/WB_PRIVATE_ACCOUNT_ID"
    floyd_counter = 5

    hashed = convert_profile_id_to_seed(string)  # expect 0x3D9C8B74
    print(f"Hashed {string} -> {hex(hashed)}")

    print(f"Shuffling counter = {floyd_counter}")
    seed_1, seed_2 = do_stuff_with_seed(hashed, floyd_counter)
    shuffler(array, seed_1, seed_2)

    shuffled = [a + 1 for a in array]
    print("Shuffled Hex", [hex(a - 1) for a in shuffled][:10])
    print("Shuffled", shuffled)

    todo = sorted(shuffled[:10])
    print("todo", todo)
