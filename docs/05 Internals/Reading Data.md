

- The reader will perform a scan of directory prefixes to determine which partitions
  need to be read.
- Each partition is self-contained and contains all of the information to process it,
  the reader will distribute the work to read partitions, there are three options:
  1) Inline - this is the simplest but the slowest, all reads are performed 
     sequentionally in the one process.
  2) Multi-process - this is usually faster than Inline, reads are distributed between
     multiple processes running on the same computer.
  3) Distributed - this isn't written yet.
- The reader will collect a list of the files in the partition, these will be:
    - data files
    - metedata files (frame.metadata)
    - index files (*.index)
    - directives (frame.invalid / frame.complete)

- The reader has the following steps:

    [partition name, columns to return, columns being filtered on, the filter (dnf)]

    - determine which frame to read (the latest complete, but not invalidated frame)
    - determine the scheme of the data from the zonemap, if there isn't one we'll fake
      one later
    - determine which blobs in the partition to read (using the zonemap, or read them
      all)
    - for each blob to be read:
        - if there's any indexes which can be used work out which rows to process
        - determine which 'driver' to use to read the blob
        - read the blob into records, selecting only the records identified after
          applying the indexes and projecting only the columns passed to the reader