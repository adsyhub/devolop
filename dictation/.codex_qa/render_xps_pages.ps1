param(
    [Parameter(Mandatory = $true)][string]$XpsPath,
    [Parameter(Mandatory = $true)][string]$OutputDirectory,
    [int]$Dpi = 144
)

$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName WindowsBase
Add-Type -AssemblyName PresentationCore
Add-Type -AssemblyName PresentationFramework
Add-Type -AssemblyName ReachFramework

$resolvedXps = (Resolve-Path -LiteralPath $XpsPath).Path
$resolvedOutput = [System.IO.Path]::GetFullPath($OutputDirectory)
[System.IO.Directory]::CreateDirectory($resolvedOutput) | Out-Null

$document = [System.Windows.Xps.Packaging.XpsDocument]::new(
    $resolvedXps,
    [System.IO.FileAccess]::Read
)

try {
    $sequence = $document.GetFixedDocumentSequence()
    $paginator = $sequence.DocumentPaginator
    $scale = $Dpi / 96.0

    for ($index = 0; $index -lt $paginator.PageCount; $index++) {
        $page = $paginator.GetPage($index)
        $width = [Math]::Max(1, [int][Math]::Ceiling($page.Size.Width * $scale))
        $height = [Math]::Max(1, [int][Math]::Ceiling($page.Size.Height * $scale))
        $bitmap = [System.Windows.Media.Imaging.RenderTargetBitmap]::new(
            $width,
            $height,
            $Dpi,
            $Dpi,
            [System.Windows.Media.PixelFormats]::Pbgra32
        )
        # Render the FixedPage visual directly. RenderTargetBitmap applies the
        # WPF DIP-to-DPI scale; a VisualBrush would use the content bounds as
        # its source box and can incorrectly stretch/crop page margins.
        $bitmap.Render($page.Visual)

        $encoder = [System.Windows.Media.Imaging.PngBitmapEncoder]::new()
        $encoder.Frames.Add([System.Windows.Media.Imaging.BitmapFrame]::Create($bitmap))
        $name = 'page-{0:D3}.png' -f ($index + 1)
        $stream = [System.IO.File]::Open(
            [System.IO.Path]::Combine($resolvedOutput, $name),
            [System.IO.FileMode]::Create,
            [System.IO.FileAccess]::Write
        )
        try {
            $encoder.Save($stream)
        }
        finally {
            $stream.Dispose()
        }
    }
    Write-Output ("Rendered {0} pages to {1}" -f $paginator.PageCount, $resolvedOutput)
}
finally {
    $document.Close()
}
