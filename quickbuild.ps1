Write-Output "I only assume current directory is the working directory"
$version = Read-Host 'What version are we on?'
Write-Output "building as latest and $version"

docker build . -t yellowjam/ai-weather-agent:latest --no-cache
docker build . -t yellowjam/ai-weather-agent:$version

$pushing = Read-Host ("Push them as well? (y|n)").ToLower()
$pushing.ToLower()

if ($pushing -eq "y" -or $pushing -eq "yes") {
    docker push yellowjam/ai-weather-agent:latest
    docker push yellowjam/ai-weather-agent:$version
}
