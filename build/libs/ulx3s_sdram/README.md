# ULX3 SDRAM for Spade

Uses litedram and a Spade stub generator.

## Usage

Perform initial setup of litedram 
```bash
swim plugin dram_setup
```

Create or modify `dram_config.yml`

Generate the litedram core and Spade stubs

```bash
swim plugign dram_generate
```

