# txtpack

A Python CLI tool for bundling and unbundling files using pattern matching,
featuring `concat` and `split` commands that preserve file integrity through byte-accurate delimiters.
The tool supports glob patterns for file selection and enables round-trip
workflows where multiple files can be concatenated into a single stream
and later reconstructed back to their original individual files.
