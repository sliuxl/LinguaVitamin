set -ex

grep cron weekly_arxiv*.yml

scripts=(
weekly_arxiv_cs.CL.yml
weekly_arxiv_cs.DC.yml
weekly_arxiv_cs.LG.yml
weekly_arxiv_cs.MA.yml
weekly_arxiv_cs.PL.yml
weekly_arxiv_cs.SE.yml
)

for item in "${scripts[@]}"; do
    diff weekly_arxiv_cs.CL.yml $item || true
done
