$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '../..')).Path
$fig=Join-Path $root 'results/figures/publication'
$app=New-Object -ComObject PowerPoint.Application
try {
 $deck=$app.Presentations.Open((Join-Path $fig 'SpaSRD_framework_editable.pptx'),$true,$false,$false)
 try { $deck.Slides.Item(1).Export((Join-Path $fig 'SpaSRD_framework_preview.png'),'PNG',2400,1350) }
 finally {$deck.Close()}
} finally {$app.Quit()}
