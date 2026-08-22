Add-Type -AssemblyName System.IO.Compression.FileSystem

$project = (Get-Location).Path
$xlsx = Join-Path $project 'lumbar_spine_mri_ai.xlsx'
$out = Join-Path $project 'lumbar_spine_mri_ai_literature_inventory.bib'

function Get-CellText($cell, $shared, $ns) {
    $formula = $cell.SelectSingleNode('./x:f', $ns)
    if ($null -ne $formula) { return $formula.InnerText }
    $v = $cell.SelectSingleNode('./x:v', $ns)
    if ($null -eq $v) { return '' }
    if ($cell.GetAttribute('t') -eq 's') { return $shared[[int]$v.InnerText] }
    return $v.InnerText
}

function BibEscape([string]$s) {
    if ([string]::IsNullOrWhiteSpace($s)) { return '' }
    $s = $s -replace '\\', '\\textbackslash{}'
    $s = $s -replace '(?<!\\)[{}]', { param($m) '\' + $m.Value }
    $s = $s -replace '(?<!\\)&', '\\&'
    $s = $s -replace '(?<!\\)%', '\\%'
    $s = $s -replace '(?<!\\)#', '\\#'
    return $s.Trim()
}

function CleanKey([string]$s) {
    $k = $s -replace '[^A-Za-z0-9]+', ''
    if ([string]::IsNullOrWhiteSpace($k)) { $k = 'paper' }
    return $k.ToLower()
}

$zip = [IO.Compression.ZipFile]::OpenRead($xlsx)
try {
    $ssXml = [xml]([IO.StreamReader]($zip.GetEntry('xl\sharedStrings.xml').Open())).ReadToEnd()
    $sheetXml = [xml]([IO.StreamReader]($zip.GetEntry('xl\worksheets\sheet1.xml').Open())).ReadToEnd()
    $ns = New-Object System.Xml.XmlNamespaceManager($sheetXml.NameTable)
    $ns.AddNamespace('x', 'http://schemas.openxmlformats.org/spreadsheetml/2006/main')
    $shared = @($ssXml.SelectNodes('//x:si', $ns) | ForEach-Object {
        ($_.SelectNodes('.//x:t', $ns) | ForEach-Object { $_.InnerText }) -join ''
    })

    $entries = New-Object System.Collections.Generic.List[string]
    $keys = @{}
    foreach ($row in $sheetXml.SelectNodes('//x:sheetData/x:row', $ns) | Select-Object -Skip 1) {
        $cells = @{}
        foreach ($cell in $row.SelectNodes('./x:c', $ns)) {
            $column = $cell.GetAttribute('r') -replace '\d', ''
            $cells[$column] = Get-CellText $cell $shared $ns
        }
        if ([string]::IsNullOrWhiteSpace($cells['D'])) { continue }

        $author = $cells['C'].Trim()
        if ([string]::IsNullOrWhiteSpace($author)) { $author = 'Unknown' }
        $year = $cells['B'].Trim()
        if ($year -notmatch '^\d{4}$') { $year = '' }
        $title = $cells['D'].Trim()
        $journal = $cells['E'].Trim()
        $primaryUrl = $cells['T'].Trim()
        $pdfFormula = $cells['Y']
        $pdfPath = ''
        if ($pdfFormula -match 'papers_pdf/[^"\)]+') { $pdfPath = $Matches[0] }
        $status = $cells['X'].Trim()

        $baseKey = (CleanKey $author) + $year + (CleanKey (($title -split '\s+')[0]))
        $key = $baseKey
        $n = 2
        while ($keys.ContainsKey($key)) { $key = $baseKey + $n; $n++ }
        $keys[$key] = $true

        $lines = @("@$('article'){$key,")
        $lines += "  author = {$((BibEscape $author))},"
        $lines += "  title = {$((BibEscape $title))},"
        if ($year) { $lines += "  year = {$year}," }
        if ($journal) { $lines += "  journal = {$((BibEscape $journal))}," }
        if ($primaryUrl -match '^https?://') { $lines += "  url = {$((BibEscape $primaryUrl))}," }
        if ($pdfPath) {
            $lines += "  file = {:$pdfPath`:PDF},"
            if ($status) { $lines += "  keywords = {$status}," }
        }
        $lines += "  note = {Source: lumbar_spine_mri_ai.xlsx},"
        $lines += "}"
        $entries.Add(($lines -join "`r`n"))
    }
}
finally { $zip.Dispose() }

$header = @(
    '% BibTeX database generated for JabRef',
    '% Source: lumbar_spine_mri_ai.xlsx',
    '% The author field follows the workbook inventory (first-author field).',
    '% PDF paths are relative to this .bib file.',
    ''
) -join "`r`n"
[IO.File]::WriteAllText($out, $header + ($entries -join "`r`n`r`n") + "`r`n", [Text.UTF8Encoding]::new($false))
Write-Output "Created $out with $($entries.Count) entries"
