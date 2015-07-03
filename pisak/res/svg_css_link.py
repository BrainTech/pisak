import os
import sys


def svg_css_link(svg_path, css_path):
    css_link = '<?xml-stylesheet type="text/css" href="{}"?>\n'.format(css_path)
    svg_file = open(svg_path, 'r+')
    lines = svg_file.readlines()
    lines.insert(1, css_link)
    svg_file.seek(0)
    svg_file.write(''.join(lines))
    svg_file.close()


if __name__ == '__main__':
    svg_folder = sys.argv[1]
    css_folder = sys.argv[2]
    for svg in os.listdir(svg_folder):
        if 'svg' in svg:
            svg_path = svg_folder + '/' + svg
            css_path = css_folder + '/' + svg[: svg.index('.')] + '.css'
            svg_css_link(svg_path, css_path)
