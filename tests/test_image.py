import os
from drivers import image

def test_image_lib_1_image_to_text():
    file = 'root/usr/share/cats.jpg'
    text = image.to_text(file)
    assert 'cat' in text

def test_image_lib_1_image_and_text_to_text():
    file = 'root/usr/share/cats.jpg'
    assert image.image_and_text_to_text(file, "What animal is this?") == 'cat'
    assert image.image_and_text_to_text(file, "What animals are these?") == 'cats'
    assert image.image_and_text_to_text(file, "How many are there") == '2'
    assert image.image_and_text_to_text(file, "How many cats are there") == '2'
    assert image.image_and_text_to_text(file, "How many dogs are there") == '0'

def test_image_bin_1_image_to_text():
    pipe = os.popen("cat root/usr/share/cats.jpg | image")
    assert 'cat' in pipe.read()

def test_image_bin_2_image_and_text_to_text():
    pipe = os.popen("cat root/usr/share/cats.jpg | image 'How many cats?'")
    assert '2' in pipe.read()
