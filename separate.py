import binascii


with open("Grp_BtlBadge.bin", "rb") as f:
    bytedata = f.read()

hexdata = binascii.hexlify(bytedata)
hexdata2 = str(hexdata).rstrip("'").strip("b'")
hexdata3 = ["00000000" + i + "" for i in hexdata2.split("7061636b")][1::]
print()
for i in range(len(hexdata3)):
    with open(f"btlbadge/{i}.bin", "wb") as file:
        file.write(binascii.unhexlify(hexdata3[i]))