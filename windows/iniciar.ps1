$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
Write-Host 'Trading Agent - SIMULACION - OKX - BTC/ETH - 4 horas'
Write-Host 'Solo se enviaran alertas mientras esta ventana permanezca abierta.'
Write-Host 'Cierra con Ctrl+C al terminar de operar.'
if (Get-Command py -ErrorAction SilentlyContinue) {
    $PythonCommand = 'py'
    $PythonArguments = @('-3')
} elseif (Get-Command python -ErrorAction SilentlyContinue) {
    $PythonCommand = 'python'
    $PythonArguments = @()
} else {
    throw 'Instala Python 3.12 o superior desde python.org y vuelve a iniciar.'
}
& $PythonCommand @PythonArguments -c 'import sys; sys.exit(0 if sys.version_info >= (3,12) else 1)'
if ($LASTEXITCODE -ne 0) { throw 'Se requiere Python 3.12 o superior.' }
if (-not $env:TELEGRAM_CHAT_ID) { $env:TELEGRAM_CHAT_ID = Read-Host 'Identificador de tu grupo de Telegram (incluye el signo menos)' }
if (-not $env:TELEGRAM_BOT_TOKEN) {
    $SecureToken = Read-Host 'Token de BotFather (oculto; no se guarda)' -AsSecureString
    $TokenPointer = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($SecureToken)
    try {
        $env:TELEGRAM_BOT_TOKEN = [Runtime.InteropServices.Marshal]::PtrToStringBSTR($TokenPointer)
    } finally {
        [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($TokenPointer)
        $SecureToken.Dispose()
    }
}
try {
    & $PythonCommand @PythonArguments -m unittest discover -s tests -q
    if ($LASTEXITCODE -ne 0) { throw 'Las pruebas fallaron; el agente no se iniciara.' }
    Write-Host 'Iniciando. No garantiza ganancias ni envia ordenes reales.'
    & $PythonCommand @PythonArguments server.py
} finally {
    Remove-Item Env:TELEGRAM_BOT_TOKEN -ErrorAction SilentlyContinue
}
