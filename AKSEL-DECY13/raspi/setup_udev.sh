#!/usr/bin/env bash
# Pemetaan tiga perangkat USB serial pada Raspberry Pi OS.
set -euo pipefail
if (( EUID != 0 )); then echo "Jalankan: sudo bash $0" >&2; exit 1; fi
command -v udevadm >/dev/null
getent group dialout >/dev/null || { echo "Grup dialout tidak ditemukan." >&2; exit 1; }
shopt -s nullglob
roles=(hmi sensor actuator)
declare -a ttys=() parents=() vendors=() products=() serials=()
declare -A identities=() endpoints=() selected=() expected=()

for dev in /dev/ttyACM* /dev/ttyUSB*; do
  [[ -c $dev ]] || continue
  tty=${dev##*/}
  parent=$(readlink -f "/sys/class/tty/$tty/device") || continue
  while [[ $parent != / && ! -r $parent/idVendor ]]; do parent=$(dirname "$parent"); done
  [[ -r $parent/idVendor && -r $parent/idProduct ]] || continue
  vid=$(<"$parent/idVendor"); pid=$(<"$parent/idProduct"); physical=${parent##*/}
  [[ $vid =~ ^[[:xdigit:]]{4}$ && $pid =~ ^[[:xdigit:]]{4}$ && $physical =~ ^[0-9]+-[0-9.]+$ ]] || continue
  sn=""
  if [[ -r $parent/serial ]]; then sn=$(<"$parent/serial"); fi
  ttys+=("$tty"); parents+=("$physical"); vendors+=("$vid"); products+=("$pid"); serials+=("$sn")
  endpoints[$physical]=$(( ${endpoints[$physical]:-0} + 1 ))
  key="$vid:$pid:$sn"; identities[$key]=$(( ${identities[$key]:-0} + 1 ))
done

if (( ${#ttys[@]} < 3 )); then echo "Hubungkan ketiga Uno terlebih dahulu." >&2; exit 1; fi
printf 'No  TTY          VID:PID    Port USB    Serial\n'
for i in "${!ttys[@]}"; do
  printf '%-3d %-12s %s:%s  %-10s %s\n' "$((i+1))" "${ttys[i]}" "${vendors[i]}" "${products[i]}" "${parents[i]}" "${serials[i]:-(kosong)}"
done

target=/etc/udev/rules.d/99-accelerator-arduinos.rules
tmp=$(mktemp -d)
staged=""
trap 'rm -rf -- "$tmp"; if [[ -n $staged ]]; then rm -f -- "$staged"; fi' EXIT
rules="$tmp/rules"
echo '# Arduino USB DECY-13. Dibuat oleh setup_udev.sh.' > "$rules"

for role in "${roles[@]}"; do
  while true; do
    read -r -p "Pilih nomor perangkat untuk $role: " choice
    [[ $choice =~ ^[1-9][0-9]?$ ]] || continue
    i=$((choice-1))
    (( i < ${#ttys[@]} )) || continue
    physical=${parents[i]}
    if (( endpoints[$physical] != 1 )); then echo "Lebih dari satu TTY pada perangkat USB ini."; continue; fi
    if [[ -n ${selected[$physical]:-} ]]; then echo "Perangkat itu sudah dipilih."; continue; fi
    break
  done
  selected[$physical]=1; expected[$role]=${ttys[i]}
  vid=${vendors[i]}; pid=${products[i]}; sn=${serials[i]}
  match="KERNELS==\"$physical\""
  if [[ $sn =~ ^[A-Za-z0-9._:-]+$ && ${identities["$vid:$pid:$sn"]} == 1 ]]; then
    read -r -p "Identitas $role: [p] port fisik (default), [s] serial unik $sn: " method
    if [[ $method == s || $method == S ]]; then match="ATTRS{serial}==\"$sn\""; fi
  else
    echo "Serial kosong, duplikat, atau tidak sesuai untuk rule. Mengikat $role ke port $physical."
  fi
  # Semua pencocokan parent mengacu pada perangkat USB yang memuat idVendor/idProduct.
  printf 'SUBSYSTEM=="tty", ATTRS{idVendor}=="%s", ATTRS{idProduct}=="%s", %s, SYMLINK+="arduino_%s", GROUP="dialout", MODE="0660"\n' \
    "$vid" "$pid" "$match" "$role" >> "$rules"
done

cat "$rules"
read -r -p "Pasang aturan tersebut? [y/N] " answer
[[ $answer == y || $answer == Y ]] || exit 0

mkdir -p /etc/udev/rules.d
if [[ -e $target ]]; then cp -p -- "$target" "$tmp/old"; fi
staged=$(mktemp /etc/udev/rules.d/.accelerator-XXXXXX)
install -m 0644 "$rules" "$staged"
mv -f -- "$staged" "$target"
staged=""

refresh() {
  udevadm control --reload-rules || return 1
  for role in "${roles[@]}"; do
    udevadm trigger --action=add --subsystem-match=tty --sysname-match="${expected[$role]}" || return 1
  done
  udevadm settle --timeout=10
}
verify() {
  for role in "${roles[@]}"; do
    alias="/dev/arduino_$role"
    [[ -L $alias && $(readlink -f "$alias") == "/dev/${expected[$role]}" ]] || return 1
    printf '%s -> %s\n' "$alias" "$(readlink -f "$alias")"
  done
}
if refresh && verify; then
  echo "Ketiga symlink terverifikasi."
else
  echo "Verifikasi gagal. Mengembalikan aturan sebelumnya." >&2
  if [[ -f $tmp/old ]]; then install -m 0644 "$tmp/old" "$target"; else rm -f -- "$target"; fi
  refresh || true
  exit 1
fi
