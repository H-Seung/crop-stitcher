from panorama import PanoramaViewerFactory

if __name__ == '__main__':
    viewer = PanoramaViewerFactory.create_viewer()
    viewer.initialize()
    viewer.run()