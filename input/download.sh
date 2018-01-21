#!/bin/bash

SAMPLE_RATE=22050
VIDEO_FORMAT=mkv
AUDIO_FORMAT=wav
SEGMENTS_FILE="eval_segments.csv"

CURRDIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
CURRDIR=$(python -c "import os.path; print(os.path.relpath('${CURRDIR}', '${PWD}'))")

# fetch_clip(videoID, startTime, endTime)
fetch_clip() {
  echo "Fetching $1 ($2 to $3)..."
  outname="$1_$2"
  if [ -f "${CURRDIR}/${outname}.${VIDEO_FORMAT}.gz" ]; then
    printf '\e[33m'
    printf 'WARNING: '
    printf '\033[0m'
    printf "File already exists ${CURRDIR}/${outname}.${VIDEO_FORMAT}.gz\n"
    printf '\e[33m'
    printf 'WARNING: '
    printf '\033[0m'
    printf "Skipping...\n"
    return
  fi

  printf '\e[33m'
  printf 'WARNING: '
  printf '\033[0m'
  printf "This may take 5-10 minutes with no indication of progress. Please be patient...\n"

  youtube-dl https://youtube.com/watch?v=$1 \
    --quiet \
    --audio-format ${AUDIO_FORMAT} \
    --recode-video ${VIDEO_FORMAT} \
    --retries infinite \
    --output "${CURRDIR}/${outname}.%(ext)s"

  if [ $? -eq 0 ]; then
    # If we don't pipe `yes`, ffmpeg seems to steal a
    # character from stdin. I have no idea why.
    yes | ffmpeg \
        -loglevel quiet \
        -i "${CURRDIR}/${outname}.${VIDEO_FORMAT}" \
        -ar ${SAMPLE_RATE} \
        -ss "$2" -to "$3" "${CURRDIR}/${outname}_out.${VIDEO_FORMAT}"
    mv "${CURRDIR}/${outname}_out.${VIDEO_FORMAT}" "${CURRDIR}/${outname}.${VIDEO_FORMAT}"
    gzip "${CURRDIR}/${outname}.${VIDEO_FORMAT}"
  else
    # Give the user a chance to Ctrl+C.
    sleep 1
  fi

  printf '\e[32m'
  printf 'SUCCESS: '
  printf '\033[0m'
  printf "Wrote ${CURRDIR}/${outname}.${VIDEO_FORMAT}.gz\n"
}

link_id="$(echo "${1}" | cut -d'=' -f 2)"
while IFS=, read -r clip_id start end rest
do
	if [ "${clip_id}" == "${link_id}" ]; then
        fetch_clip ${clip_id} ${start} ${end}
		exit 0
	fi
done < "${CURRDIR}/${SEGMENTS_FILE}"

printf '\e[31m'
printf 'ERROR: '
printf '\033[0m'
printf "Unable to download clip '${1}' matched in '${CURRDIR}/${SEGMENTS_FILE}'.\n" 
printf '\e[31m'
printf 'ERROR: '
printf '\033[0m'
printf "Are you sure you copied it correctly?\n"
exit 1
