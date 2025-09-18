from panorama import PanoramaViewerFactory

if __name__ == '__main__':
    viewer = PanoramaViewerFactory.create_viewer(config_path='config_20250917_133505_manual.yaml')
    viewer.initialize()
    viewer.run()