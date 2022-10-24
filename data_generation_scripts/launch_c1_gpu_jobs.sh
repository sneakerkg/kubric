# Echo GPU id
echo "$1"
for ((i=0;i<200;i++))
do
    docker run --gpus "device=$1" --env NVIDIA_DISABLE_REQUIRE=1 --rm --interactive --volume "$(pwd):/kubric" 436622332146.dkr.ecr.us-east-2.amazonaws.com/lablet-others:kubruntu_with_cuda /usr/bin/python3 challenges/movi/c1_worker.py --job_dir "./c1_2k/gpu$1/$i"
done