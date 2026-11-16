param([string]$DocumentName = 'SpaSRD_V5多方法图文统一修订稿.docx', [string]$QaName = 'qa')
$ErrorActionPreference = 'Stop'
$root = Split-Path (Split-Path $PSScriptRoot -Parent) -Parent
$inputDoc = Join-Path (Join-Path $root 'results/manuscript') $DocumentName
$qaPath = Join-Path (Join-Path $root 'results/manuscript') $QaName
New-Item -ItemType Directory -Force -Path $qaPath | Out-Null
$wordApp = New-Object -ComObject Word.Application
$wordApp.Visible = $false
$wordApp.DisplayAlerts = 0
try {
    $openedDoc = $wordApp.Documents.Open($inputDoc, $false, $true)
    try {
        $openedDoc.Repaginate()
        $openedDoc.ExportAsFixedFormat((Join-Path $qaPath 'word_render.pdf'),17)
        Write-Output ('Pages: ' + $openedDoc.ComputeStatistics(2))
    } finally { $openedDoc.Close(0) }
} finally {
    $wordApp.Quit()
    [System.Runtime.InteropServices.Marshal]::ReleaseComObject($wordApp) | Out-Null
}
