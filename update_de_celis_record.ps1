$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.IO.Compression.FileSystem

$root = Get-Location
$input = Join-Path $root 'lumbar_spine_mri_ai_literature_inventory_PDF_links_and_title_author_check.xlsx'
$output = Join-Path $root 'lumbar_spine_mri_ai_literature_inventory_PDF_links_and_title_author_check_updated.xlsx'
$work = Join-Path ([IO.Path]::GetTempPath()) ('decelis_' + [Guid]::NewGuid().ToString('N'))

[IO.Compression.ZipFile]::ExtractToDirectory($input, $work)
$sheetPath = Join-Path $work 'xl\worksheets\sheet1.xml'
$sheet = Get-Content -Raw -LiteralPath $sheetPath

function Set-CellText([string]$xml, [string]$ref, [string]$value) {
  $safe = [System.Security.SecurityElement]::Escape($value)
  $pattern = '(?s)<x:c r="' + $ref + '"[^>]*>.*?</x:c>'
  $replacement = '<x:c r="' + $ref + '" s="15" t="str"><x:v>' + $safe + '</x:v></x:c>'
  return [regex]::Replace($xml, $pattern, $replacement, 1)
}

$sheet = Set-CellText $sheet 'C82' 'Garcia de Celis'
$sheet = Set-CellText $sheet 'D82' 'Deep Learning-Based Lumbar Spinal Canal Stenosis Classification Using MRI Scans'
$sheet = Set-CellText $sheet 'Z82' 'Match'
$sheet = Set-CellText $sheet 'AA82' 'Verified from the PDF: Guillermo Garcia de Celis; Wisam Bukaita, Ph.D.'

[IO.File]::WriteAllText($sheetPath, $sheet, [Text.UTF8Encoding]::new($false))
if (Test-Path -LiteralPath $output) { Remove-Item -LiteralPath $output -Force }
[IO.Compression.ZipFile]::CreateFromDirectory($work, $output)
Remove-Item -LiteralPath $work -Recurse -Force
Write-Output "Updated row 81 in $output"
