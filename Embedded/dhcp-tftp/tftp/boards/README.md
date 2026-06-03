Coloque aqui scripts U-Boot por placa, por exemplo:
  boards/board1/boot.scr
  boards/board2/boot.scr
Gere com:
  mkimage -A riscv -T script -C none -n 'board1 boot' -d board1.cmd boot.scr
