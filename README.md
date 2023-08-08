# segyio_header_buf
segyio header Field.buf always big endian?

Investigation into the `segyio.field.Field.buf` byteorder. It was expected that the raw bytes of the header would match the byteorder of the segy file, i.e. `endian` parameter in the `segyio.open()` context manager. However, it doesn't appear to do so. Two segy files were created: (1) simply reads in the first five traces and writes out the bytes with the original byteorder, and (2) changes the byteorder to little endian (system native byteorder). When converting the `buf` raw bytes class variable to python integer objects, the *little endian* file required *big endian* decoding to get the correct value.

- `create_example_segy_big_ibm.py`: creates first 5 traces with original byteorder, no formatting
- `create_example_segy_little_ieee.py`: creates first 5 traces with little endian byteorder

The examples use [segytools](https://github.com/anthonytorlucci/segytools) to parse the raw segy binary data for reading and reformatting in the case of the *little* endian segy.

## open source data
[dataunderground penobscot](https://dataunderground.org/dataset/penobscot) - Penobscot_3D_gathers_part1/3D_gathers_pstm_nmo_X1001.sgy

## version
```python
import segyio
print(segyio.__version__)
# 1.9.3
```
