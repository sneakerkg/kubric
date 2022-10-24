# Echo GPU id
echo "$1"
for ((i=0;i<200;i++))
do
    docker run --rm --interactive   --user $(id -u):$(id -g)      --volume "$(pwd):/kubric"     kubricdockerhub/kubruntu /usr/bin/python3 challenges/movi/c1_worker.py --job_dir "./c1_2k_test/cpu$1/$i"
done