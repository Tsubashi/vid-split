"""The Splitter Class."""
from dataclasses import dataclass
from pathlib import Path

from ..helpers.ParallelFFmpeg import ParallelFFmpeg
from ..helpers import ffprogress
from ..helpers import cover_utils


@dataclass
class Splitter:
    """Holds all the info and methods for splitting a file."""
    input_path: Path
    output_dir_path: Path
    segment_list: list

    buffer: float = 0.0
    output_pattern: str = "segment_{i:04d}.mp3"

    def split(self):
        """Do the actual splitting."""
        # Generate task list
        tasks = list()
        segment_files = list()
        for i, segment in enumerate(self.segment_list):
            # Apply buffer
            start = segment.start_time - self.buffer
            end = segment.end_time + self.buffer
            time = end - start

            self.output_dir_path.mkdir(exist_ok=True)
            output_path = self.output_dir_path / self.output_pattern.format(i, i=i, title=segment.title)
            segment_files.append(output_path)

            cmd = ["ffmpeg", "-ss", str(start), "-t", str(time), "-i", self.input_path,
                   "-c:v", "copy", "-map_chapters", "-1", "-y"]
            if segment.title:
                cmd.extend(["-metadata", f"title={segment.title}"])
            cmd.append(output_path)

            name = f"Splitting segment {i}"
            if segment.title:
                name += f" - {segment.title}"
            tasks.append({
                "name": name,
                "command": cmd
            })

        # Process splits in parallel
        p = ParallelFFmpeg(f"Splitting '{self.input_path.name}'")
        p.process(tasks)

        # Create a unified file
        filelist_file = self.output_dir_path / "filelist"
        with open(filelist_file, 'w') as f:
            for file in segment_files:
                # Single quotes in filenames need to be replaced with `'\''` to work with ffmpeg
                # https://superuser.com/questions/787064/filename-quoting-in-ffmpeg-concat
                safer_filename = str(file).replace("'", "'\\''")
                f.write(f"file '{safer_filename}'\n")

        # Then use that file to concatenate everything.
        output_file = self.output_dir_path / self.output_pattern.format(i, i=9999, title="combined")
        cmd = ["ffmpeg", "-f", "concat", "-safe", "0", "-i", filelist_file, "-c", "copy", output_file]
        ffprogress.run(cmd, "Combining Audio Files.")




