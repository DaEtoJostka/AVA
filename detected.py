

if __name__ == "__main__":
    import argparse

    def parse_arguments() -> argparse.Namespace:
        """Parse command-line arguments."""
        parser = argparse.ArgumentParser(description='YOLO Video Detection and Compression')
        parser.add_argument('--input_video', required=True, help='Path to the input video file')
        parser.add_argument('--output_video', required=True, help='Path to save the output video file')
        parser.add_argument('--compressed_video', required=True, help='Path to save the compressed video file')
        parser.add_argument('--annotations', default='annotations.csv', help='Path to save the annotations CSV file')
        return parser.parse_args()

    args = parse_arguments()
    main(args.input_video, args.output_video, args.compressed_video, args.annotations)